# -*- coding: utf-8 -*-
"""Management, capital stock, underwriting and closing sections."""

SECTIONS = [("MANAGEMENT", [
 ("h2", "Executive Officers and Directors"),
 ("p", "The following table sets forth information regarding our executive officers and directors as of the date of this prospectus:"),
 ("table", [
  ["Name", "Position"],
  ["Zhong Hao", "Founder, Chief Executive Officer, Chief Architect and Chairman of the Board"],
  ["Zelin Wu", "Co-Founder, Director and Engineering Lead, Client Applications"],
  ["Junwei Chen", "Co-Founder, Director and Engineering Lead, Relay Infrastructure"],
  ["Junqiao Chen", "Co-Founder, Director and Engineering Lead, Platform Engineering"],
 ], [2.2 * 72, 4.1 * 72]),
 ("p", "<b>Zhong Hao</b> is our founder and has served as our Chief Executive Officer, Chief Architect and Chairman since our inception. Mr. Zhong conceived the ECNUchat platform and led the design and implementation of its cryptographic protocol stack, including the post-quantum hybrid X3DH handshake, the hybrid Double Ratchet, the signed hash-chained group state mechanism and the platform’s adversarial test program. He is the principal author of the platform’s technical documentation and protocol analyses. We believe Mr. Zhong’s deep technical command of the platform and of the applied-cryptography research literature qualifies him to serve on our board of directors."),
 ("p", "<b>Zelin Wu</b> is a co-founder of ECNUchat and a member of the founding engineering team that designed and built the platform, with responsibility for the client applications, including the desktop and terminal interfaces that share the platform’s session engine."),
 ("p", "<b>Junwei Chen</b> is a co-founder of ECNUchat and a member of the founding engineering team, with responsibility for the relay server and store — the components that hold public keys, signed prekeys and sealed envelopes and that validate signatures on all key material before acceptance."),
 ("p", "<b>Junqiao Chen</b> is a co-founder of ECNUchat and a member of the founding engineering team, with responsibility for platform engineering, including the encrypted attachment pipeline and the automated protocol and security test suite."),
 ("h2", "Board Composition and Governance"),
 ("p", "Our board of directors consists of four members, all of whom are founders. Following the completion of this offering, we intend to appoint additional directors, including directors who qualify as independent under the listing standards of the Nasdaq Global Market, and to establish an audit committee, a compensation committee and a nominating and corporate governance committee, each composed in accordance with applicable SEC and Nasdaq requirements, subject to the phase-in periods available to newly public companies and emerging growth companies. As a result of our dual-class structure, we expect to be a “controlled company” under Nasdaq rules and may elect exemptions from certain corporate governance requirements; if we do so, we will disclose that election in our periodic reports."),
 ("h2", "Code of Business Conduct and Ethics"),
 ("p", "We have adopted a code of business conduct and ethics applicable to our directors, officers and employees, which will be available on our website upon completion of this offering. We intend to disclose any amendments to, or waivers from, the code as required by applicable law."),
 ("h2", "Executive Compensation"),
 ("p", "As an emerging growth company, we are providing reduced executive compensation disclosure. During our development stage, our named executive officers received no cash compensation from the Company, and their interests are held through Class B common stock. The following table summarizes compensation for our principal executive officer for the period from inception through [•], 2026:"),
 ("table", [
  ["Name and Principal Position", "Salary ($)", "All Other Compensation ($)", "Total ($)"],
  ["Zhong Hao, Chief Executive Officer", "—", "—", "—"],
 ], [2.5 * 72, 1.2 * 72, 1.5 * 72, 1.1 * 72]),
 ("h2", "Limitation of Liability and Indemnification"),
 ("p", "Our certificate of incorporation limits the liability of our directors and officers to the fullest extent permitted by the Delaware General Corporation Law and provides for indemnification of our directors and officers against certain liabilities. We have entered into indemnification agreements with each of our directors and executive officers and intend to maintain directors’ and officers’ liability insurance following this offering."),
])]

SECTIONS += [("PRINCIPAL STOCKHOLDERS", [
 ("p", "The following table sets forth information regarding the beneficial ownership of our common stock as of [•], 2026, by (i) each person known to us to beneficially own more than 5% of our common stock, (ii) each of our directors and named executive officers, and (iii) all of our directors and executive officers as a group. Beneficial ownership is determined in accordance with SEC rules. Except as indicated, each person has sole voting and investment power over the shares shown."),
 ("table", [
  ["Name", "Class B Shares", "Percent of Total Voting Power (Before Offering)", "Percent of Total Voting Power (After Offering)"],
  ["Zhong Hao", "[•]", "[•]%", "[•]%"],
  ["Zelin Wu", "[•]", "[•]%", "[•]%"],
  ["Junwei Chen", "[•]", "[•]%", "[•]%"],
  ["Junqiao Chen", "[•]", "[•]%", "[•]%"],
  ["All directors and executive officers as a group (4 persons)", "[•]", "[•]%", "[•]%"],
 ], [1.9 * 72, 1.2 * 72, 1.7 * 72, 1.6 * 72]),
 ("p", "Immediately following this offering, our founders will hold all outstanding shares of Class B common stock and will control a majority of the combined voting power of our capital stock. See “Risk Factors — Our dual-class structure concentrates control with our founders.”"),
])]

SECTIONS += [("RELATED PARTY TRANSACTIONS", [
 ("p", "Since our inception, we have not entered into any transactions, and there are no currently proposed transactions, in which we were or are a participant, the amount involved exceeds $120,000, and any related person had or will have a direct or indirect material interest, other than the issuance of Class B common stock to our founders at inception and indemnification agreements described under “Management.” We have adopted a policy requiring that any related party transaction be reviewed and approved by our audit committee or another independent body of our board of directors."),
])]

SECTIONS += [("DESCRIPTION OF CAPITAL STOCK", [
 ("p", "The following description summarizes the material terms of our capital stock as set forth in our amended and restated certificate of incorporation and bylaws, which will be effective upon the closing of this offering. This description is qualified in its entirety by reference to those documents, copies of which are filed as exhibits to the registration statement of which this prospectus forms a part."),
 ("h2", "General"),
 ("p", "Our authorized capital stock consists of [•] shares of Class A common stock, par value $0.0001 per share, [•] shares of Class B common stock, par value $0.0001 per share, and [•] shares of preferred stock, par value $0.0001 per share, the rights of which may be established by our board of directors without further stockholder approval."),
 ("h2", "Class A and Class B Common Stock"),
 ("p", "<b>Voting.</b> Each share of Class A common stock entitles its holder to one vote; each share of Class B common stock entitles its holder to ten votes. The holders vote together as a single class on all matters submitted to stockholders, except as otherwise required by law. <b>Dividends and liquidation.</b> The Class A and Class B common stock share ratably in dividends and in distributions upon liquidation, subject to any preferential rights of preferred stock then outstanding. <b>Conversion.</b> Each share of Class B common stock is convertible at any time, at the holder’s option, into one share of Class A common stock, and converts automatically upon certain transfers and upon the date on which the outstanding Class B common stock first represents less than the threshold specified in our certificate of incorporation. Class A common stock is not convertible into Class B common stock. <b>Other rights.</b> Neither class has preemptive, redemption or sinking fund rights."),
 ("h2", "Anti-Takeover Provisions"),
 ("p", "Our certificate of incorporation and bylaws contain provisions that may delay, defer or prevent a change of control, including a classified board of directors, the elimination of stockholder action by written consent, advance notice procedures for director nominations and stockholder proposals, and the authority of the board to issue preferred stock with rights senior to the common stock. Section 203 of the Delaware General Corporation Law also restricts business combinations with interested stockholders. These provisions could discourage acquisition proposals that our stockholders might consider favorable."),
 ("h2", "Exclusive Forum"),
 ("p", "Our certificate of incorporation provides that the Court of Chancery of the State of Delaware will be the exclusive forum for certain derivative and fiduciary-duty actions, and that the federal district courts will be the exclusive forum for actions arising under the Securities Act of 1933, in each case to the fullest extent permitted by law."),
 ("h2", "Listing and Transfer Agent"),
 ("p", "We have applied to list our Class A common stock on the Nasdaq Global Market under the symbol “ECNC.” Our Class B common stock will not be listed. The transfer agent and registrar for our Class A common stock is [•]."),
])]

SECTIONS += [("SHARES ELIGIBLE FOR FUTURE SALE", [
 ("p", "Following this offering, we will have [•] shares of Class A common stock outstanding (assuming conversion of Class B shares only as described herein) and [•] shares of Class B common stock outstanding, convertible into the same number of shares of Class A common stock. The shares sold in this offering will be freely tradable without restriction under the Securities Act, except that shares purchased by our affiliates will be subject to the volume and other limitations of Rule 144."),
 ("p", "Our directors, officers and existing stockholders have entered into lock-up agreements with the underwriters agreeing, subject to certain exceptions, not to sell or otherwise dispose of shares of our common stock for a period of 180 days following the date of this prospectus without the prior written consent of the representatives of the underwriters. After the expiration of these lock-up agreements, shares held by our founders will be eligible for sale subject to Rule 144 and the conversion of Class B common stock into Class A common stock upon sale."),
 ("p", "We intend to file a registration statement on Form S-8 to register shares reserved under our equity incentive plans. No prediction can be made as to the effect, if any, that future sales of shares, or the availability of shares for future sale, will have on the market price of our Class A common stock."),
])]

SECTIONS += [("MATERIAL U.S. FEDERAL INCOME TAX CONSIDERATIONS", [
 ("p", "The following is a summary of material U.S. federal income tax considerations of the acquisition, ownership and disposition of our Class A common stock by a holder that is not a United States person for U.S. federal income tax purposes. This summary is based on the Internal Revenue Code of 1986, as amended, Treasury regulations and administrative and judicial interpretations, all as in effect on the date of this prospectus and subject to change. It does not address all tax considerations that may be relevant to a particular holder, and holders are urged to consult their own tax advisors."),
 ("p", "Dividends paid by us, if any, to a non-U.S. holder generally will be subject to withholding tax at a rate of 30%, unless reduced by an applicable income tax treaty or effectively connected with a U.S. trade or business. Gain realized by a non-U.S. holder on the sale of our Class A common stock generally will not be subject to U.S. federal income tax unless the gain is effectively connected with a U.S. trade or business or we are or have been a U.S. real property holding corporation, which we do not expect to be the case. Special backup withholding and information reporting rules may apply in certain circumstances."),
])]

SECTIONS += [("UNDERWRITING", [
 ("p", "[•], [•] and [•] are acting as joint book-running managers of this offering and as representatives of the underwriters. Subject to the terms and conditions of the underwriting agreement, each underwriter has severally agreed to purchase the number of shares of Class A common stock set forth opposite its name below at the public offering price, less the underwriting discount:"),
 ("table", [
  ["Underwriter", "Number of Shares"],
  ["[•]", "[•]"],
  ["[•]", "[•]"],
  ["[•]", "[•]"],
  ["Total", "[•]"],
 ], [3.3 * 72, 2.7 * 72]),
 ("p", "The underwriters propose to offer the shares directly to the public at the initial public offering price set forth on the cover of this prospectus and to certain dealers at a concession not in excess of $[•] per share. The underwriters have an option, exercisable within 30 days of the date of this prospectus, to purchase up to [•] additional shares from us at the initial public offering price, less underwriting discounts and commissions, solely to cover over-allotments."),
 ("p", "We estimate that the total underwriting discounts and commissions payable by us will be $[•] per share and $[•] in total, and that total offering expenses payable by us will be approximately $[•]. We have agreed to indemnify the underwriters against certain liabilities, including liabilities under the Securities Act, or to contribute to payments that the underwriters may be required to make in respect of those liabilities."),
 ("p", "Our directors, officers and existing stockholders have agreed, for a period of 180 days after the date of this prospectus and subject to certain exceptions, not to offer, sell, pledge or otherwise dispose of any shares of our common stock without the prior written consent of the representatives. In connection with this offering, the underwriters may engage in stabilizing transactions, over-allotment transactions, syndicate covering transactions and penalty bids in accordance with Regulation M under the Exchange Act. A prospectus in electronic format may be made available on the websites maintained by one or more of the underwriters."),
])]

SECTIONS += [("LEGAL MATTERS", [
 ("p", "The validity of the Class A common stock offered by this prospectus will be passed upon for us by [•], and certain legal matters will be passed upon for the underwriters by [•]."),
])]

SECTIONS += [("EXPERTS", [
 ("p", "The consolidated financial statements of ECNUchat, Inc. as of and for the period ended [•], 2026, included in this prospectus, have been audited by [•], an independent registered public accounting firm, as stated in their report appearing herein, and are included in reliance upon such report given on the authority of such firm as experts in accounting and auditing."),
])]

SECTIONS += [("WHERE YOU CAN FIND MORE INFORMATION", [
 ("p", "We have filed with the SEC a registration statement on Form S-1 under the Securities Act with respect to the shares of Class A common stock offered by this prospectus. This prospectus, which constitutes part of the registration statement, does not contain all of the information set forth in the registration statement, some items of which are contained in exhibits to the registration statement. You may inspect and copy the registration statement, including the exhibits, at the SEC’s Public Reference Room and through the SEC’s website at www.sec.gov."),
 ("p", "Upon completion of this offering, we will be subject to the information reporting requirements of the Securities Exchange Act of 1934 and will file annual, quarterly and current reports, proxy statements and other information with the SEC. We intend to make these filings available on our investor relations website at [•]. The information on our website is not part of this prospectus."),
])]

SECTIONS += [("INDEX TO FINANCIAL STATEMENTS", [
 ("p", "ECNUchat, Inc. — Consolidated Financial Statements (development-stage company). Page references: Report of Independent Registered Public Accounting Firm — F-2; Consolidated Balance Sheet as of [•], 2026 — F-3; Consolidated Statement of Operations for the period from inception to [•], 2026 — F-4; Consolidated Statement of Stockholders’ Equity — F-5; Consolidated Statement of Cash Flows — F-6; Notes to Consolidated Financial Statements — F-7."),
 ("h2", "Report of Independent Registered Public Accounting Firm (Placeholder)"),
 ("p", "[To be completed by amendment upon inclusion of audited financial statements. In a preliminary prospectus, this section sets forth the framework of the financial statements to be audited in accordance with the standards of the Public Company Accounting Oversight Board (United States).]"),
 ("h2", "Consolidated Balance Sheet (Framework)"),
 ("table", [
  ["(in thousands)", "As of [•], 2026"],
  ["Cash and cash equivalents", "$[•]"],
  ["Total assets", "$[•]"],
  ["Total liabilities", "$[•]"],
  ["Class A common stock, $0.0001 par value", "$[•]"],
  ["Class B common stock, $0.0001 par value", "$[•]"],
  ["Additional paid-in capital", "$[•]"],
  ["Accumulated deficit", "$([•])"],
  ["Total stockholders’ equity", "$[•]"],
 ], [3.4 * 72, 2.6 * 72]),
 ("h2", "Notes to Consolidated Financial Statements (Summary of Significant Policies)"),
 ("p", "<b>Organization and basis of presentation.</b> ECNUchat, Inc. was incorporated in Delaware in 2026 to hold and commercialize the ECNUchat encrypted messaging platform. The Company is a development-stage enterprise; it has generated no revenue and its operations to date consist of platform research and development. The financial statements are prepared in accordance with U.S. GAAP."),
 ("p", "<b>Use of estimates.</b> The preparation of financial statements in conformity with U.S. GAAP requires management to make estimates and assumptions that affect reported amounts. Actual results could differ from those estimates."),
 ("p", "<b>Going concern.</b> Management evaluates whether conditions raise substantial doubt about the Company’s ability to continue as a going concern within one year of the issuance of the financial statements, taking into account the expected proceeds of this offering."),
 ("p", "<b>Research and development.</b> Research and development costs are expensed as incurred. Software developed for internal use and for the Company’s platform is evaluated under applicable guidance; to date, all such costs have been expensed."),
 ("center", "— End of Prospectus —"),
])]
