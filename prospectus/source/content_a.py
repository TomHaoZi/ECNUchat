# -*- coding: utf-8 -*-
"""Front matter, summary, and offering sections."""

COVER_PARAS = [
 "This is the initial public offering of shares of Class A common stock of ECNUchat, Inc. We are offering 50,000,000 shares of our Class A common stock. Prior to this offering, there has been no public market for our Class A common stock. The initial public offering price is expected to be between $28.00 and $32.00 per share. See “Underwriting” for additional information regarding the terms of this offering.",
 "We have two classes of common stock outstanding: Class A common stock and Class B common stock. The rights of the holders of Class A common stock and Class B common stock are identical, except with respect to voting and conversion. Each share of Class A common stock is entitled to one vote per share. Each share of Class B common stock is entitled to ten votes per share and is convertible into one share of Class A common stock at any time at the option of the holder or upon certain transfers. Our founders hold all of our outstanding Class B common stock and will, following this offering, continue to control a majority of the voting power of our outstanding capital stock. See “Description of Capital Stock.”",
 "We are an “emerging growth company” as defined under the federal securities laws. As an emerging growth company, we may take advantage of certain exemptions from various reporting requirements that are applicable to other public companies, including reduced disclosure obligations regarding executive compensation and exemptions from the auditor attestation requirements of Section 404 of the Sarbanes-Oxley Act of 2002. See “Risk Factors” and “Management’s Discussion and Analysis of Financial Condition and Results of Operations.”",
 "The underwriters have an option, exercisable within 30 days from the date of this prospectus, to purchase up to an additional 7,500,000 shares of Class A common stock from us at the initial public offering price, less underwriting discounts and commissions, solely to cover over-allotments, if any.",
]

COVER_TABLE = [("table", [
 ["", "Per Share", "Total"],
 ["Public offering price", "$30.00", "$1,500,000,000"],
 ["Underwriting discounts and commissions", "$2.10", "$105,000,000"],
 ["Proceeds, before expenses, to us", "$27.90", "$1,395,000,000"],
], [3.4 * 72, 1.3 * 72, 1.3 * 72])]

INSIDE_FRONT = [
 ("legend", "A registration statement relating to these securities has been filed with the Securities and Exchange Commission but has not yet become effective. These securities may not be sold, nor may offers to buy be accepted, prior to the time the registration statement becomes effective. This prospectus is not an offer to sell these securities and it is not soliciting an offer to buy these securities in any jurisdiction where the offer or sale is not permitted."),
 ("h2", "About This Prospectus"),
 ("p", "This prospectus is part of a registration statement on Form S-1 that we filed with the Securities and Exchange Commission (the “SEC”) using a “shelf” registration process. You should read this prospectus and the related registration statement carefully and in their entirety, including the financial statements and the exhibits and schedules to the registration statement, before deciding whether to invest in our Class A common stock."),
 ("p", "You should rely only on the information contained in this prospectus or to which we have referred you. We have not authorized anyone to provide you with information that is different from that contained in this prospectus. This prospectus may only be used where it is legal to sell these securities. The information in this prospectus is accurate only as of the date of this prospectus, regardless of the time of delivery of this prospectus or of any sale of our Class A common stock. Our business, financial condition, results of operations and prospects may have changed since that date."),
 ("h2", "Industry and Market Data"),
 ("p", "This prospectus includes industry and market data that we obtained from third-party sources, industry publications and our own internal estimates. Although we believe these sources are reliable, we have not independently verified the information and cannot guarantee its accuracy or completeness. Our internal estimates are based on information obtained from our management and other sources that we believe to be reliable, but such estimates involve risks and uncertainties and are subject to change."),
 ("h2", "Trademarks and Trade Names"),
 ("p", "This prospectus contains references to our trademarks and service marks, including “ECNUchat” and our logo. All other trademarks, service marks and trade names appearing in this prospectus are the property of their respective owners. We do not intend our use of or reference to other parties’ trademarks to imply any endorsement of, or affiliation with, such parties, and the inclusion of any such references is not intended to imply that such parties endorse this offering."),
 ("h2", "A Note on the Name “ECNUchat”"),
 ("p", "Our platform originated as an academic research project in applied cryptography conducted under the name “ECNUchat,” a reference to East China Normal University in Shanghai, where the project was first developed. We are not affiliated with, sponsored by, or endorsed by East China Normal University, and no securities are being offered by or on behalf of the university."),
]

TOC_TITLES = [
 "PROSPECTUS SUMMARY",
 "RISK FACTORS",
 "SPECIAL NOTE REGARDING FORWARD-LOOKING STATEMENTS",
 "USE OF PROCEEDS",
 "DIVIDEND POLICY",
 "CAPITALIZATION",
 "DILUTION",
 "SELECTED CONSOLIDATED FINANCIAL AND OPERATING DATA",
 "MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS",
 "BUSINESS",
 "INDUSTRY OVERVIEW",
 "MANAGEMENT",
 "PRINCIPAL STOCKHOLDERS",
 "RELATED PARTY TRANSACTIONS",
 "DESCRIPTION OF CAPITAL STOCK",
 "SHARES ELIGIBLE FOR FUTURE SALE",
 "MATERIAL U.S. FEDERAL INCOME TAX CONSIDERATIONS",
 "UNDERWRITING",
 "LEGAL MATTERS",
 "EXPERTS",
 "WHERE YOU CAN FIND MORE INFORMATION",
 "INDEX TO FINANCIAL STATEMENTS",
]

SECTIONS = []

SECTIONS += [("PROSPECTUS SUMMARY", [
 ("p", "This summary highlights selected information contained elsewhere in this prospectus. This summary does not contain all of the information that you should consider before deciding to invest in our Class A common stock. You should read this entire prospectus carefully, including the sections entitled “Risk Factors,” “Selected Consolidated Financial and Operating Data” and “Management’s Discussion and Analysis of Financial Condition and Results of Operations” and our consolidated financial statements and the related notes thereto included elsewhere in this prospectus, before making an investment decision."),
 ("h2", "ECNUchat, Inc."),
 ("p", "<b>Our mission is to make private communication a property of mathematics, not a promise made by a platform.</b> ECNUchat is an end-to-end encrypted messaging platform in which the servers that carry traffic are never able to read it. Our relay infrastructure transports sealed envelopes between users; the cryptographic keys that open those envelopes are generated on, and never leave, users’ own devices. Unlike conventional messaging services, where confidentiality depends on the operator’s policies, internal access controls and resistance to legal compulsion, our architecture is designed so that there is nothing readable for an operator — or an attacker who compromises the operator — to disclose."),
 ("p", "Our platform implements, end to end and in production-quality code, the protocol stack that the cryptographic research community has developed and analyzed over the past decade: the X3DH key agreement protocol extended with a post-quantum key encapsulation mechanism in the PQXDH design; the Double Ratchet algorithm, extended so that every new ratchet chain additionally mixes in a fresh post-quantum shared secret; AES-256-GCM authenticated encryption for every individual message; and, for group conversations, per-recipient pairwise encryption with a signed, hash-chained group membership state. Our post-quantum components use ML-KEM-768, the module-lattice key encapsulation mechanism standardized by the U.S. National Institute of Standards and Technology in FIPS 203 (August 2024). As a result, conversations on our platform are protected not only against interception today, but also against the “harvest now, decrypt later” strategy in which an adversary records ciphertext today in order to decrypt it with a future cryptographically relevant quantum computer."),
 ("p", "The ECNUchat platform comprises approximately 20,000 lines of Python across its protocol engine, relay server and two client applications — a desktop application and a terminal application that share a single session engine — together with a web-based (PWA) client generation and a relay network design in our second-generation architecture. The protocol core is covered by an automated test suite of 95 test functions, including adversarial tests that simulate a malicious relay server substituting keys, replaying envelopes, tampering with ciphertext and forging group membership; the platform ships with reproducible attack-demonstration programs that let any evaluator verify these properties independently."),
 ("h2", "The Problem We Address"),
 ("p", "Billions of people conduct their personal, commercial and professional lives over messaging systems whose confidentiality rests on institutional trust. In the dominant architectures, message content is either unencrypted in transit between server components, encrypted with keys the operator holds, or protected by protocols whose metadata exposure and group-security properties fall short of what the research literature recommends. At the same time, the migration to post-quantum cryptography has become urgent for any communication expected to remain confidential for years: intelligence and criminal organizations are widely believed to be archiving encrypted traffic today for future decryption. A messaging platform that is merely “encrypted” by present-day standards may therefore already be compromised as a long-term store of confidential communication."),
 ("h2", "Our Technology"),
 ("bullet", "<b>Post-quantum hybrid key establishment.</b> New conversations are established with X3DH — four X25519 Diffie-Hellman operations whose outputs are combined through HKDF-SHA256 — extended, following the PQXDH design analyzed by Fiedler and Günther (PKC 2025), with an ML-KEM-768 encapsulation against signed long-term and one-time post-quantum prekeys. Where both endpoints support the hybrid protocol, classical-only handshakes are rejected, so a network intermediary cannot silently strip the post-quantum component."),
 ("bullet", "<b>A ratchet that never stands still.</b> Every message is encrypted under its own AES-256-GCM key derived from the Double Ratchet algorithm (analyzed in the universally composable framework by Bienstock et al., CRYPTO 2022), providing forward secrecy for the past and self-healing security for the future. Our hybrid extension re-encapsulates a fresh ML-KEM shared secret into every new ratchet chain, so post-quantum protection is renewed continuously rather than only at session setup."),
 ("bullet", "<b>Groups without a shared sender key.</b> Group messages are fanned out as individually ratcheted envelopes to each recipient — a design chosen in direct response to the group-messaging weaknesses identified by Rösler, Mainka and Schwenk (IEEE EuroS and P 2018) — and group membership is maintained as a signed, hash-chained state that a malicious server cannot forge, fork or roll back undetected."),
 ("bullet", "<b>Encrypted everything.</b> Attachments up to 8 GiB are transferred in 8 MiB chunks under a second AES-256-GCM layer; voice messages and end-to-end encrypted voice calls (whose call keys are delivered inside ratchet envelopes) are supported; private keys at rest are sealed in a local vault derived from the user’s password with PBKDF2-HMAC-SHA256 at 600,000 iterations."),
 ("bullet", "<b>Verifiable by design.</b> Identity fingerprints (the SHA-256 hash of a user’s signing identity key) let users detect key substitution out of band. Our relay servers store only public keys, signed prekeys and sealed envelopes, and our open-source codebase, published protocol analyses and attack demonstrations allow independent experts to audit every security claim we make."),
 ("h2", "Our Strengths"),
 ("bullet", "<b>Security that does not depend on trusting us.</b> Our threat model assumes the relay operator may be malicious. The platform’s confidentiality and integrity properties are enforced by client-side cryptography, not by our policies."),
 ("bullet", "<b>Post-quantum by default, today.</b> While incumbent platforms have deployed post-quantum protection at initial key agreement only, or not at all, our hybrid design extends post-quantum key material into both session establishment and ongoing ratcheting."),
 ("bullet", "<b>Research-grade foundations.</b> Each layer of our stack corresponds to a peer-reviewed construction — X3DH/PQXDH, the Double Ratchet, and signed group state — and our implementation tracks the published security analyses, including their stated limitations, rather than inventing proprietary cryptography."),
 ("bullet", "<b>Capital-efficient architecture.</b> Because relays handle only ciphertext, our infrastructure requirements are modest, content-moderation data liabilities are structurally minimized, and our open-source development model compounds external review at no marginal cost."),
 ("h2", "Our Strategy"),
 ("p", "Our strategy is to (i) complete and harden the second-generation platform, including the web client and multi-relay federation; (ii) grow a user base among privacy-sensitive individuals, journalists, legal and healthcare professionals, and enterprises with confidential-communication obligations; (iii) introduce paid tiers for organizations — managed relay hosting, compliance archiving under customer-held keys, and priority infrastructure — that monetize operations rather than message content, which we are architecturally unable to read; and (iv) continue publishing our protocol work and independent security evaluations to make verifiable privacy the basis of competition in our market."),
 ("h2", "Risks Associated with Our Business"),
 ("p", "Our business is subject to a number of risks, including the following, which are described more fully under “Risk Factors”:"),
 ("bullet", "We are a development-stage company with no operating revenue to date, a short operating history and an unproven business model; we expect to incur substantial losses for the foreseeable future."),
 ("bullet", "Our value proposition depends entirely on the correctness of our cryptography. A vulnerability in our protocols or implementation could destroy user trust, which is our principal asset."),
 ("bullet", "We compete with very large, well-capitalized platform companies that distribute encrypted messaging to billions of users at no charge."),
 ("bullet", "Encryption technologies are subject to evolving and sometimes conflicting regulation, export controls and lawful-access demands across jurisdictions, including in China, where our principal operations are located."),
 ("bullet", "Our dual-class capital structure concentrates voting control with our founders, and our Class A common stock has no prior public market and may be volatile."),
 ("h2", "Corporate Information"),
 ("p", "We were incorporated in the State of Delaware in 2026 under the name ECNUchat, Inc., to hold and commercialize the ECNUchat platform, which was originally developed as an academic research project in applied cryptography. Our principal executive offices are located in Shanghai, China. Our website address is www.ecnuchat.com. The information contained on, or accessible through, our website is not a part of this prospectus. We are an “emerging growth company” and, as such, have elected to comply with certain reduced public company disclosure requirements."),
 ("h2", "The Offering"),
 ("table", [
  ["", ""],
  ["Class A common stock offered by us", "50,000,000 shares"],
  ["Option to purchase additional shares", "The underwriters have an option, exercisable for 30 days, to purchase up to 7,500,000 additional shares of Class A common stock from us solely to cover over-allotments, if any."],
  ["Class A common stock outstanding immediately after this offering", "200,000,000 shares"],
  ["Class B common stock outstanding immediately after this offering", "400,000,000 shares (convertible into Class A common stock on a one-for-one basis; ten votes per share)"],
  ["Voting rights", "Each share of Class A common stock is entitled to one vote; each share of Class B common stock is entitled to ten votes. The Class A and Class B common stock vote together as a single class on all matters, except as required by law."],
  ["Use of proceeds", "We intend to use the net proceeds for general corporate purposes, including research and development, relay infrastructure, working capital and potential acquisitions. See “Use of Proceeds.”"],
  ["Proposed Nasdaq Global Market symbol", "“ECNC”"],
  ["Risk factors", "See “Risk Factors” and other information included in this prospectus for a discussion of factors you should consider before deciding to invest in our Class A common stock."],
 ], [1.9 * 72, 4.4 * 72]),
 ("p", "Unless otherwise indicated, the information in this prospectus assumes (i) no exercise of the underwriters’ option to purchase additional shares, (ii) the conversion of all outstanding convertible securities as described herein, and (iii) an initial public offering price of $30.00 per share, the midpoint of the range set forth on the cover of this prospectus."),
 ("h2", "Summary Consolidated Financial and Operating Data"),
 ("p", "We were formed in 2026 and have not generated revenue. Our activities to date have consisted of developing the ECNUchat platform, and our historical financial statements, which will be included in this prospectus at the page referenced in the table of contents under “Index to Financial Statements,” should be read in conjunction with “Selected Consolidated Financial and Operating Data” and “Management’s Discussion and Analysis of Financial Condition and Results of Operations.” The summary balance sheet data below is presented on an actual basis and on an as-adjusted basis giving effect to this offering, and is qualified in its entirety by reference to those sections."),
 ("table", [
  ["(in thousands)", "Actual", "As Adjusted"],
  ["Cash and cash equivalents", "$9,640", "$1,386,640"],
  ["Total assets", "$9,950", "$1,386,950"],
  ["Total liabilities", "$310", "$310"],
  ["Total stockholders’ equity", "$9,640", "$1,386,640"],
 ], [2.6 * 72, 1.7 * 72, 1.7 * 72]),
])]

SECTIONS += [("RISK FACTORS", [
 ("p", "Investing in our Class A common stock involves a high degree of risk. You should carefully consider the risks described below, together with all of the other information included in this prospectus, including our consolidated financial statements and the related notes, before deciding whether to purchase our Class A common stock. The risks described below are not the only ones facing our company. Additional risks or uncertainties not presently known to us, or that we currently deem immaterial, may also impair our business operations. If any of the following risks occur, our business, financial condition, results of operations and prospects would likely suffer. In that event, the market price of our Class A common stock could decline, and you could lose all or part of your investment."),
 ("h2", "Risks Related to Our Business and Industry"),
 ("risk", "We are a development-stage company with no revenue, a limited operating history and an unproven business model.",
  "We were formed in 2026 to commercialize a platform that originated as an academic research project. We have not generated any revenue, have incurred and expect to continue to incur substantial operating losses, and have not yet demonstrated that users or organizations will pay for our planned services. Our planned monetization — organizational relay hosting, customer-key compliance archiving and premium infrastructure — is untested, and our inability to read message content forecloses advertising and data-driven business models available to competitors. If we fail to develop a viable revenue model, we may be unable to sustain operations."),
 ("risk", "Secure messaging exhibits powerful network effects, and we compete with entrenched platforms with billions of users.",
  "A messaging service is useful in proportion to the number of a user’s contacts who also use it. Signal, WhatsApp, Telegram, iMessage and WeChat, among others, are distributed at no charge by organizations with vastly greater financial, engineering and marketing resources than ours, and several already offer end-to-end encryption by default. Users may be unwilling to persuade their contacts to adopt an additional application, however strong its security properties, and our growth could stall regardless of the quality of our technology."),
 ("risk", "Our growth depends on users understanding and valuing technical security properties that are difficult to evaluate.",
  "Post-quantum hybrid key agreement, forward secrecy and self-healing security are not visible features. Most users cannot distinguish our architecture from marketing claims made by competitors, and adoption driven by security reputation may be slow, episodic or dependent on third-party endorsements and press coverage that we cannot control."),
 ("risk", "If we are unable to attract, retain and motivate qualified personnel, our business will suffer.",
  "Applied cryptography engineering talent is scarce and intensely recruited. Our founding team is small, our operations are centered in Shanghai, and our ability to hire senior protocol engineers, security auditors and infrastructure engineers is critical to executing our roadmap, including multi-device support, sealed-sender metadata protection and header encryption, none of which our platform currently provides."),
 ("risk", "Our platform may be used for unlawful purposes, which could expose us to legal, regulatory and reputational harm.",
  "Because we cannot read message content, we cannot moderate it. Our service may be used by persons engaged in unlawful activity, and governments, media or payment and distribution partners may attribute that activity to us, demand capabilities our architecture does not have, or restrict our distribution. Compliance demands that require content access are existential for a platform whose defining property is the absence of such access."),
 ("risk", "We depend on third-party distribution channels, libraries and infrastructure.",
  "Our desktop and terminal clients are built on third-party frameworks, including PySide6 and the Python cryptography library, and our web client depends on browser platform capabilities. Changes to application store policies, browser APIs, library maintenance or licensing could impair our ability to distribute or operate the platform. Our relay design assumes commodity hosting; loss of hosting providers willing to carry encrypted relay traffic would increase costs."),
 ("h2", "Risks Related to Our Technology and Security"),
 ("risk", "A flaw in our cryptographic protocols or their implementation could destroy the trust on which our business depends.",
  "Our entire value proposition is the correctness of our cryptography. The protocols we implement have been analyzed in the academic literature under stated assumptions; our implementation has not been formally verified, and published analyses of the Double Ratchet identify residual windows — including the period during which a sending ratchet private key must be retained pending the peer’s next ratchet public key — that our implementation, consistent with the literature, does not eliminate. A single exploitable flaw, whether in our code, in an underlying library or in a future revision of the underlying standards, could expose historical or future communications and irreparably damage our reputation."),
 ("risk", "The post-quantum transition creates both our opportunity and a material technical risk.",
  "We rely on ML-KEM-768 as standardized in FIPS 203. Cryptographic standards evolve: parameter sets, encodings or recommended algorithms may change, weaknesses may be discovered in lattice-based schemes, and interoperability expectations may shift. Conversely, if cryptographically relevant quantum computers arrive sooner than expected, any conversation conducted before our hybrid protections were active — including on competing platforms — may be retrospectively decrypted, with unpredictable consequences for user trust in encrypted messaging generally, including ours."),
 ("risk", "Our security model has known, disclosed limitations that competitors or critics may characterize unfavorably.",
  "Our relay servers necessarily learn communication metadata: who communicates with whom, when, and the size of envelopes. Our current design does not implement sealed-sender metadata protection, message-header encryption, or multi-device synchronization, and group membership additions are recorded in a signed chain while member removal is not yet supported by the chain’s monotonic design. Sophisticated adversaries — including state-level actors capable of global network observation — may exploit metadata even where content remains protected."),
 ("risk", "Security incidents, including compromise of our relay infrastructure or signing keys, could harm our business.",
  "Although relay servers store only public keys and sealed envelopes, a compromised relay can deny service, delay or drop envelopes, or attempt key substitution against users who have not verified fingerprints. Compromise of our software release or code-signing process could distribute malicious clients, which no protocol design can withstand. We may not detect incidents promptly, and our resources for incident response are limited."),
 ("risk", "Our open-source model may limit our ability to capture value and may assist competitors.",
  "Our codebase is publicly available under an open-source license. Competitors and third parties may operate compatible or forked services without contributing to our development, may identify vulnerabilities in public code before our users have updated, and may commercialize our work in ways that compete with our paid offerings."),
 ("h2", "Risks Related to Regulation and Our Operations in China"),
 ("risk", "Encryption is heavily regulated, and regulations differ and conflict across jurisdictions.",
  "Our technology is subject to export control regimes, including the U.S. Export Administration Regulations, and to encryption-specific laws in multiple jurisdictions that may require licensing, source-code disclosure, or the provision of decryption assistance. China’s Cryptography Law, Cybersecurity Law, Data Security Law and Personal Information Protection Law impose requirements on cryptographic products and data handling that may conflict with obligations imposed elsewhere. Changes in any of these regimes, or in their enforcement, could require us to alter our architecture, restrict our service geographically, or cease operations in a market."),
 ("risk", "Governments may mandate lawful-access capabilities incompatible with our architecture.",
  "Legislative proposals in several jurisdictions would require messaging providers to scan, retain or make accessible message content. Because our servers never possess readable content or the keys to obtain it, compliance with such mandates could be technically impossible without abandoning end-to-end encryption, which is the foundation of our business."),
 ("risk", "Our principal operations are in China, which exposes us to political, legal and economic risks.",
  "Changes in U.S.–China relations, including tariffs, sanctions, investment restrictions and scrutiny of China-based issuers by U.S. regulators and exchanges, could impair our ability to access U.S. capital markets, retain our listing, or operate across borders. Our financial statements are prepared in accordance with U.S. GAAP; the regulatory environment for China-based issuers, including inspection of audit work papers, has historically been contentious and may affect investor perception regardless of our individual circumstances."),
 ("risk", "Privacy and data protection laws impose obligations we may fail to meet.",
  "Although our architecture minimizes personal data — our relays store public keys, signed prekeys and sealed envelopes, and message content never reaches us — account metadata and operational logs remain subject to regimes such as the EU General Data Protection Regulation and China’s Personal Information Protection Law. Violations could result in fines, orders restricting processing, and reputational harm."),
 ("h2", "Risks Related to This Offering and Our Class A Common Stock"),
 ("risk", "There has been no prior public market for our Class A common stock, and the market price may be volatile.",
  "An active trading market may not develop or be sustained. The initial public offering price will be negotiated with the underwriters and may bear no relationship to the price at which our stock trades after this offering. Broad market fluctuations, announcements concerning cryptography or quantum computing, and our own operating results may cause substantial volatility."),
 ("risk", "Our dual-class structure concentrates control with our founders and limits your ability to influence corporate matters.",
  "Our founders hold all outstanding Class B common stock, which carries ten votes per share, and will control a majority of the combined voting power following this offering. This concentration may delay or prevent a change of control, deter acquisition proposals that other stockholders might consider favorable, and cause the market price of our Class A common stock to be lower than it would be absent such concentration."),
 ("risk", "We are an emerging growth company and have elected reduced disclosure, which may make our stock less attractive.",
  "We are an emerging growth company under the JOBS Act and are exempt from certain reporting requirements, including the auditor attestation requirement of Section 404 of the Sarbanes-Oxley Act. Reduced disclosure may make it harder for investors to evaluate our business and may depress the price of our Class A common stock."),
 ("risk", "You will suffer immediate and substantial dilution.",
  "Investors purchasing shares in this offering will pay a price substantially higher than the net tangible book value per share of our existing stockholders and will experience immediate dilution of $27.69 per share, with the possibility of further dilution from future issuances, option exercises and the conversion of Class B common stock."),
 ("risk", "We have broad discretion over the use of proceeds and may not use them effectively.",
  "Our management will have considerable discretion in applying the net proceeds of this offering. We currently intend to use them for general corporate purposes, but the actual allocation may differ materially, and investments made with the proceeds may not yield a return."),
 ("risk", "Provisions in our charter and bylaws and under Delaware law could discourage a takeover that stockholders may consider favorable.",
  "Our certificate of incorporation and bylaws include provisions such as a classified board of directors, limitations on stockholder action by written consent, and advance notice requirements for nominations and proposals. These provisions, together with Section 203 of the Delaware General Corporation Law, may make it more difficult for a third party to acquire us."),
 ("risk", "We do not intend to pay dividends, so returns will depend entirely on appreciation in the price of our Class A common stock.",
  "We have never declared or paid dividends and intend to retain all available funds for the development of our business. If our stock does not appreciate, you may not realize a return on your investment."),
])]

SECTIONS += [("SPECIAL NOTE REGARDING FORWARD-LOOKING STATEMENTS", [
 ("p", "This prospectus contains forward-looking statements within the meaning of Section 27A of the Securities Act of 1933, as amended, and Section 21E of the Securities Exchange Act of 1934, as amended. Forward-looking statements include, among other things, statements regarding our future results of operations and financial position, our business strategy, our planned products and services, the anticipated capabilities and benefits of our technology, market trends, and our objectives for future operations. You can identify forward-looking statements by the use of words such as “anticipate,” “believe,” “could,” “estimate,” “expect,” “intend,” “may,” “plan,” “potential,” “predict,” “project,” “should,” “will” and similar expressions."),
 ("p", "Forward-looking statements are based on our management’s beliefs and assumptions and on information currently available to management. Although we believe that the expectations reflected in these statements are reasonable, they involve known and unknown risks, uncertainties and other factors that may cause our actual results to differ materially, including those described under “Risk Factors.” You should not place undue reliance on forward-looking statements. We undertake no obligation to update or revise any forward-looking statements, whether as a result of new information, future events or otherwise, except as required by law."),
])]

SECTIONS += [("USE OF PROCEEDS", [
 ("p", "We estimate that the net proceeds to us from this offering will be approximately $1,377.0 million (or approximately $1,586.3 million if the underwriters exercise in full their option to purchase additional shares), assuming an initial public offering price of $30.00 per share, which is the midpoint of the price range set forth on the cover of this prospectus, after deducting underwriting discounts and commissions and estimated offering expenses payable by us."),
 ("p", "We intend to use the net proceeds of this offering for general corporate purposes, including: (i) research and development, including completion of our second-generation platform, multi-device support, metadata protection and independent security audits; (ii) expansion and hardening of our relay infrastructure; (iii) sales, marketing and user acquisition; and (iv) working capital and other general corporate purposes. We may also use a portion of the proceeds to acquire or invest in complementary businesses, products or technologies, although we have no present agreements or commitments to do so."),
 ("p", "Pending their use, we intend to invest the net proceeds in short-term, investment-grade, interest-bearing securities. The amounts and timing of our actual expenditures will depend on numerous factors, and our management will have broad discretion in the application of the net proceeds."),
])]

SECTIONS += [("DIVIDEND POLICY", [
 ("p", "We have never declared or paid any cash dividends on our capital stock, and we do not anticipate declaring or paying any cash dividends in the foreseeable future. We intend to retain all available funds and any future earnings to fund the development and growth of our business. Any future determination to declare cash dividends will be made at the discretion of our board of directors and will depend on our financial condition, results of operations, capital requirements, contractual restrictions and other factors our board deems relevant."),
])]

SECTIONS += [("CAPITALIZATION", [
 ("p", "The following table sets forth our cash and cash equivalents and capitalization as of October 31, 2026, on an actual basis and on an as-adjusted basis giving effect to the sale of shares in this offering at an assumed initial public offering price of $30.00 per share, after deducting underwriting discounts and commissions and estimated offering expenses. You should read this table together with our consolidated financial statements and the related notes and “Management’s Discussion and Analysis of Financial Condition and Results of Operations” included elsewhere in this prospectus."),
 ("table", [
  ["(in thousands, except share data)", "Actual", "As Adjusted"],
  ["Cash and cash equivalents", "$9,640", "$1,386,640"],
  ["Class A common stock, $0.0001 par value", "$15", "$20"],
  ["Class B common stock, $0.0001 par value", "$40", "$40"],
  ["Additional paid-in capital", "$12,485", "$1,389,480"],
  ["Accumulated deficit", "$(2,900)", "$(2,900)"],
  ["Total stockholders’ equity", "$9,640", "$1,386,640"],
  ["Total capitalization", "$9,640", "$1,386,640"],
 ], [2.9 * 72, 1.5 * 72, 1.6 * 72]),
])]

SECTIONS += [("DILUTION", [
 ("p", "Investors who purchase shares of Class A common stock in this offering will experience immediate and substantial dilution in the net tangible book value of their investment. Our net tangible book value as of October 31, 2026 was $9,640,000, or $0.02 per share. After giving effect to this offering, our as-adjusted net tangible book value would be $1,386,640,000, or $2.31 per share. This represents an immediate increase in net tangible book value of $2.29 per share to existing stockholders and an immediate dilution of $27.69 per share to new investors. The following table illustrates this dilution on a per-share basis:"),
 ("table", [
  ["", "Per Share"],
  ["Assumed initial public offering price", "$30.00"],
  ["Net tangible book value per share before this offering", "$0.02"],
  ["Increase per share attributable to new investors", "$2.29"],
  ["As-adjusted net tangible book value per share after this offering", "$2.31"],
  ["Dilution per share to new investors", "$27.69"],
 ], [4.3 * 72, 1.7 * 72]),
 ("p", "The table above excludes 12,500,000 shares of Class A common stock issuable upon the exercise of outstanding options and 2,000,000 shares issuable upon the settlement of restricted stock units. To the extent such securities are exercised or settled, there will be further dilution to new investors."),
])]

SECTIONS += [("SELECTED CONSOLIDATED FINANCIAL AND OPERATING DATA", [
 ("p", "We were incorporated in 2026 and, as of the date of this prospectus, have not generated revenue. Our selected consolidated financial data is derived from our audited consolidated financial statements included elsewhere in this prospectus. Historical results are not necessarily indicative of results to be expected in future periods. The data below should be read in conjunction with “Capitalization,” “Management’s Discussion and Analysis of Financial Condition and Results of Operations” and our consolidated financial statements and the related notes."),
 ("table", [
  ["(in thousands)", "Period from Inception (March 2, 2026) to October 31, 2026"],
  ["Revenue", "$—"],
  ["Research and development expense", "$1,940"],
  ["General and administrative expense", "$960"],
  ["Net loss", "$(2,900)"],
  ["Cash and cash equivalents, end of period", "$9,640"],
 ], [3.1 * 72, 2.9 * 72]),
 ("p", "As a development-stage company, our operating data to date consists principally of platform development milestones rather than commercial metrics. As of the date of this prospectus, our platform comprises approximately 20,000 lines of code, a 95-function automated security and protocol test suite, desktop and terminal clients sharing a single session engine, and a second-generation web client and relay architecture in development. We do not currently charge users, and we had no paying customers as of the date of this prospectus."),
])]

SECTIONS += [("MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS", [
 ("p", "The following discussion and analysis of our financial condition and results of operations should be read together with our consolidated financial statements and the related notes appearing elsewhere in this prospectus. This discussion contains forward-looking statements that involve risks and uncertainties. Our actual results could differ materially from those anticipated in these forward-looking statements as a result of various factors, including those discussed under “Risk Factors.”"),
 ("h2", "Overview"),
 ("p", "ECNUchat, Inc. is a development-stage company formed in 2026 to commercialize an end-to-end encrypted messaging platform that originated as an academic research project. We have not generated revenue since inception. Our activities to date have consisted of designing, implementing and testing our protocol stack — post-quantum hybrid key establishment, the hybrid Double Ratchet, per-recipient group encryption with signed group state, encrypted attachments and encrypted voice — and the client and relay software that delivers it. We expect to incur increasing operating expenses as we complete our second-generation platform, submit our implementation to independent security audit, expand our relay infrastructure and build the organizational services through which we intend to generate revenue."),
 ("h2", "Basis of Presentation"),
 ("p", "Our consolidated financial statements have been prepared in accordance with accounting principles generally accepted in the United States of America. Our fiscal year ends on December 31. As an emerging growth company, we have elected to use the extended transition period for complying with new or revised financial accounting standards and to be exempt from the auditor attestation requirements of Section 404 of the Sarbanes-Oxley Act."),
 ("h2", "Components of Results of Operations"),
 ("p", "<b>Revenue.</b> We have not generated revenue to date. We expect our initial revenue, if any, to come from organizational services — managed relay hosting, customer-key compliance archiving and premium infrastructure — rather than from consumer subscriptions or advertising, which our architecture does not support because we cannot access message content."),
 ("p", "<b>Research and development expenses.</b> These consist primarily of personnel costs for protocol and client engineering, independent security review, and development infrastructure. We expect research and development expenses to increase substantially as we complete our second-generation platform and undertake multi-device support and metadata-protection work."),
 ("p", "<b>General and administrative expenses.</b> These consist of personnel costs for executive, legal, finance and administrative functions, professional fees (including the costs of being a public company), and facilities costs. We expect these expenses to increase following this offering."),
 ("p", "<b>Cost of revenue (future).</b> When we commence paid services, cost of revenue will consist principally of relay hosting and bandwidth costs, which we expect to remain modest relative to conventional messaging platforms because our relays process ciphertext only and perform no content-related computation."),
 ("h2", "Liquidity and Capital Resources"),
 ("p", "Since inception, we have financed our operations through founder contributions and the proceeds of this offering will constitute our principal source of liquidity. We believe that the net proceeds of this offering, together with our existing cash, will be sufficient to fund our operations for at least the next twelve months following the date of this prospectus. Our future capital requirements will depend on the pace of platform development, the cost of independent security audits, user growth and the associated relay capacity, and our ability to generate revenue from organizational services. We may seek additional capital through equity or debt financings, which may not be available on acceptable terms, or at all."),
 ("h2", "Critical Accounting Policies and Estimates"),
 ("p", "Our management’s discussion and analysis is based on our consolidated financial statements, which have been prepared in accordance with U.S. GAAP. The preparation of these financial statements requires us to make estimates and assumptions that affect the reported amounts of assets, liabilities and expenses. Significant areas include the valuation of equity awards and the assessment of our ability to continue as a going concern. Actual results may differ from these estimates under different assumptions or conditions."),
])]
