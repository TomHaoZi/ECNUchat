import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.awt.GraphicsEnvironment;
import java.io.IOException;
import java.io.InputStream;
import java.net.BindException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.swing.JOptionPane;

/** Offline Windows host for the bundled PWA. The browser owns the client identity. */
public class Desktop {
    private static final String LOOPBACK = "127.0.0.1";

    private static String setting(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? fallback : value.trim();
    }

    private static Path browser() throws IOException {
        String explicit = setting("ECNU_DESKTOP_BROWSER", "");
        if (!explicit.isEmpty()) return Path.of(explicit);
        for (String vendor : new String[]{"Microsoft/Edge/Application/msedge.exe",
                                          "Google/Chrome/Application/chrome.exe"}) {
            for (String location : new String[]{"ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"}) {
                String root = System.getenv(location);
                if (root == null) continue;
                Path candidate = Path.of(root).resolve(vendor);
                if (Files.isRegularFile(candidate)) return candidate;
            }
        }
        throw new IOException("Microsoft Edge or Google Chrome is required. You can set ECNU_DESKTOP_BROWSER to its executable.");
    }

    private static String relayOverride() throws Exception {
        String env = setting("ECNU_RELAY_URL", "");
        if (!env.isEmpty() || setting("ECNU_DESKTOP_CONFIG", "").isEmpty()) return env;
        // Select only the relay URL from JSON. Other configuration fields stay on disk.
        Path powershell = Path.of(System.getenv("SystemRoot"), "System32", "WindowsPowerShell",
                                  "v1.0", "powershell.exe");
        String read = """
            $ErrorActionPreference = 'Stop'
            [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
            $json = [IO.File]::ReadAllText($env:ECNU_DESKTOP_CONFIG) | ConvertFrom-Json
            if ($null -ne $json.relayUrl -and $json.relayUrl -isnot [string]) { exit 1 }
            [Console]::Write($json.relayUrl)
            """;
        Process reader = new ProcessBuilder(powershell.toString(), "-NoProfile", "-NonInteractive",
                "-Command", read).redirectError(ProcessBuilder.Redirect.DISCARD).start();
        String url;
        try (InputStream data = reader.getInputStream()) {
            url = new String(data.readAllBytes(), StandardCharsets.UTF_8);
        }
        if (reader.waitFor() != 0) throw new IOException("Cannot read relayUrl from ECNU_DESKTOP_CONFIG.");
        return url.trim();
    }

    private static Map<String, byte[]> assets() throws Exception {
        Map<String, byte[]> files = new HashMap<>();
        try (ZipInputStream zip = new ZipInputStream(Desktop.class.getResourceAsStream("/pwa.zip"))) {
            for (ZipEntry entry; (entry = zip.getNextEntry()) != null; ) {
                if (!entry.isDirectory()) files.put("/" + entry.getName(), zip.readAllBytes());
            }
        }
        String encoded = Base64.getEncoder().encodeToString(relayOverride().getBytes(StandardCharsets.UTF_8));
        try (InputStream config = Desktop.class.getResourceAsStream("/config.js")) {
            String bridge = new String(config.readAllBytes(), StandardCharsets.UTF_8) + """

                window.ECNUDesktop = Object.freeze({
                  resolveRelayUrl: function(stored) {
                    var override = new TextDecoder().decode(Uint8Array.from(atob('%s'), function(c) { return c.charCodeAt(0); }));
                    return resolveRelayUrl({envRelayUrl: override, storedRelayUrl: stored});
                  }
                });
                """.formatted(encoded);
            files.put("/desktop-bridge.js", bridge.getBytes(StandardCharsets.UTF_8));
        }
        return files;
    }

    private static String contentType(String path) {
        if (path.endsWith(".js")) return "text/javascript; charset=utf-8";
        if (path.endsWith(".html")) return "text/html; charset=utf-8";
        if (path.endsWith(".css")) return "text/css; charset=utf-8";
        if (path.endsWith(".json")) return "application/json; charset=utf-8";
        if (path.endsWith(".png")) return "image/png";
        if (path.endsWith(".svg")) return "image/svg+xml";
        if (path.endsWith(".md") || path.contains("/LICENSE-")) return "text/plain; charset=utf-8";
        return "application/octet-stream";
    }

    private static void serve(HttpExchange exchange, String authority, Map<String, byte[]> files) throws IOException {
        try (exchange) {
            if (!authority.equals(exchange.getRequestHeaders().getFirst("Host"))) {
                exchange.sendResponseHeaders(403, -1);
                return;
            }
            String method = exchange.getRequestMethod();
            if (!method.equals("GET") && !method.equals("HEAD")) {
                exchange.getResponseHeaders().set("Allow", "GET, HEAD");
                exchange.sendResponseHeaders(405, -1);
                return;
            }
            String path = exchange.getRequestURI().getRawPath();
            if (path.equals("/")) path = "/index.html";
            byte[] body = files.get(path);
            if (body == null) {
                exchange.sendResponseHeaders(404, -1);
                return;
            }
            var headers = exchange.getResponseHeaders();
            headers.set("Content-Type", contentType(path));
            headers.set("Cache-Control", "no-store");
            headers.set("X-Content-Type-Options", "nosniff");
            headers.set("X-Frame-Options", "DENY");
            headers.set("Content-Length", Integer.toString(body.length));
            exchange.sendResponseHeaders(200, method.equals("HEAD") ? -1 : body.length);
            if (method.equals("GET")) exchange.getResponseBody().write(body);
        }
    }

    private static void run(boolean serveOnly) throws Exception {
        int port = Integer.parseInt(setting("ECNU_DESKTOP_PORT", "38765"));
        if (port < 1 || port > 65535) throw new IOException("ECNU_DESKTOP_PORT must be between 1 and 65535.");
        Map<String, byte[]> files = assets();
        String authority = LOOPBACK + ":" + port;
        HttpServer server;
        try {
            server = HttpServer.create(new InetSocketAddress(InetAddress.getByName(LOOPBACK), port), 64);
        } catch (BindException e) {
            throw new IOException("Unable to open " + authority + ". Close the other desktop instance or free this port.", e);
        }
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            server.createContext("/", exchange -> serve(exchange, authority, files));
            server.setExecutor(workers);
            server.start();
            try {
                if (serveOnly) {
                    new CountDownLatch(1).await();
                } else {
                    Path profile = Path.of(setting("ECNU_DESKTOP_PROFILE", Path.of(System.getenv("LOCALAPPDATA"),
                            "ECNUchat", "v2", "EdgeProfile").toString())).toAbsolutePath().normalize();
                    Files.createDirectories(profile);
                    Process window = new ProcessBuilder(browser().toString(), "--app=http://" + authority + "/",
                            "--user-data-dir=" + profile, "--no-first-run", "--no-default-browser-check",
                            "--disable-background-mode", "--disable-background-networking", "--disable-component-update",
                            "--disable-sync", "--disable-features=msEdgeStartupBoost,msEdgeFirstRunExperience")
                            .redirectOutput(ProcessBuilder.Redirect.DISCARD)
                            .redirectError(ProcessBuilder.Redirect.DISCARD).start();
                    if (window.waitFor() != 0) throw new IOException("The browser process exited with an error.");
                }
            } finally {
                server.stop(0);
            }
        }
    }

    public static void main(String[] args) {
        boolean serveOnly = args.length == 1 && args[0].equals("--serve-only");
        try {
            if (args.length != 0 && !serveOnly) throw new IOException("Supported optional argument: --serve-only");
            run(serveOnly);
        } catch (Exception e) {
            System.err.println(e.getMessage());
            if (!serveOnly && !GraphicsEnvironment.isHeadless()) {
                JOptionPane.showMessageDialog(null, e.getMessage(), "ECNUchat v2", JOptionPane.ERROR_MESSAGE);
            }
            System.exit(1);
        }
    }
}
