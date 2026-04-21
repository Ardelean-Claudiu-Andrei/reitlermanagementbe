import html
from datetime import datetime
from weasyprint import HTML as WeasyprintHTML

# ─── Translations ─────────────────────────────────────────────────────────────

T = {
    "ro": {
        "offerFor": "OFERTĂ PENTRU",
        "to": "Către",
        "offerDate": "Data ofertei:",
        "regNo": "Nr. înreg.:",
        "intro": "În urma cererii dumneavoastră, avem plăcerea de a vă face cunoscută oferta noastră de preț:",
        "colNo": "Nr.\nCrt.",
        "colName": "Denumire reper",
        "colQty": "Buc",
        "colUnit": "Preț unitar\n(€)",
        "colTotal": "Preț total\n(€)",
        "grandTotal": "Preț Total (EURO):",
        "priceNote": "Prețurile de mai sus sunt exprimate în EURO și nu conțin TVA",
        "conditionsTitle": "Condiții generale",
        "deliveryLabel": "Termen livrare:",
        "deliveryWeeks": "săptămâni",
        "notIncludeLabel": "Prețurile nu conțin:",
        "notInclude": [
            "fundația silozurilor, dimensionarea rigidizărilor necesare la stabiliment, lucrări de construcție, zidărie",
            "lucrările cu racordul electric principal",
            "măsurătorile pentru rezistență și izolare",
            "cheltuielile apărute în timpul punerii în funcțiune și a probei (materiale, energie, personal)",
            "cheltuielie cu macaraua de la fața locului (în cazul silozurilor exterioare: 2 macarale / zi, precum și necesarul de macarale pentru descărcare – 1 macara)",
            "cheltuielile suplimentare în cazul apariției întârzierilor din culpa beneficiarului, acestea vor fi suportate de beneficiar",
        ],
        "warrantyLabel": "Garanție:",
        "warrantyText": "Utilajele noi din prezenta ofertă beneficiază de o garanție de 24 luni",
        "serviceText": "Pentru service post – garanție al utilajelor de prezenta ofertă se va întocmi un contract de service",
        "paymentLabel": "Condiții de plată:",
        "payment1": "50 % + TVA la semnarea contractului",
        "payment2": "40 % + TVA după transportul utilajelor",
        "payment3": "10 % + TVA după montaj și semnarea procesului verbal de predare-primire",
        "validityLabel": "Valabilitate ofertă:",
        "validity21": "21 de zile de la data prezentei oferte",
        "before": "Înainte de lansarea comenzii vor fi clarificate toate aspectele tehnice.",
        "contact": "Pentru nelămuriri sau informații suplimentare, vă stăm la dispoziție.",
        "review": "Vă rugăm să ne anunțați după analizarea ofertei noastre.",
        "regards": "Cu stimă,",
        "installation": "Manopera de montaj",
        "installationSub": "Cazare, transport personal, etc.",
    },
    "hu": {
        "offerFor": "AJÁNLAT",
        "to": "Részére",
        "offerDate": "Ajánlat dátuma:",
        "regNo": "Reg. szám:",
        "intro": "Az Ön megkeresése alapján örömmel tájékoztatjuk Önt árajánlatunkról:",
        "colNo": "Ssz.",
        "colName": "Megnevezés",
        "colQty": "db",
        "colUnit": "Egységár\n(€)",
        "colTotal": "Összár\n(€)",
        "grandTotal": "Összár (EURO):",
        "priceNote": "A fenti árak EURO-ban vannak megadva és nem tartalmazzák az ÁFÁ-t",
        "conditionsTitle": "Általános feltételek",
        "deliveryLabel": "Szállítási idő:",
        "deliveryWeeks": "hét",
        "notIncludeLabel": "Az árak nem tartalmazzák:",
        "notInclude": [
            "a silók alapozása, a merevítések méretezése, építési és falazási munkák",
            "a fővillamos csatlakozóra vonatkozó munkák",
            "ellenállás- és szigetelési mérések",
            "az üzembe helyezés és a próba során felmerülő kiadások (anyagok, energia, személyzet)",
            "helyszíni daruzási költségek (külső silók esetén: 2 daru/nap, valamint a lerakáshoz szükséges daruigény – 1 daru)",
            "a megrendelő hibájából eredő késedelmek esetén felmerülő többletköltségek, ezeket a megrendelő viseli",
        ],
        "warrantyLabel": "Garancia:",
        "warrantyText": "A jelen ajánlatban szereplő új gépek 24 hónap garanciát élveznek",
        "serviceText": "A jelen ajánlatban szereplő berendezések garancia utáni szervizéhez szervizszerződés kerül megkötésre",
        "paymentLabel": "Fizetési feltételek:",
        "payment1": "50% + ÁFA a szerződés aláírásakor",
        "payment2": "40% + ÁFA a gépek szállítása után",
        "payment3": "10% + ÁFA a szerelés és az átadás-átvételi jegyzőkönyv aláírása után",
        "validityLabel": "Az ajánlat érvényessége:",
        "validity21": "21 nap a jelen ajánlat dátumától",
        "before": "A megrendelés leadása előtt minden műszaki szempontot tisztázni kell.",
        "contact": "Kérdések vagy további információk esetén rendelkezésére állunk.",
        "review": "Kérjük, értesítsen minket ajánlatunk elemzése után.",
        "regards": "Tisztelettel,",
        "installation": "Szerelési munkadíj",
        "installationSub": "Szállás, személyzet szállítása, stb.",
    },
    "de": {
        "offerFor": "ANGEBOT FÜR",
        "to": "An",
        "offerDate": "Angebotsdatum:",
        "regNo": "Reg.-Nr.:",
        "intro": "In Folge Ihrer Anfrage haben wir die Freude, Ihnen unser Preisangebot bekannt zu geben:",
        "colNo": "Nr.",
        "colName": "Bezeichnung",
        "colQty": "Stk",
        "colUnit": "Einzelpreis\n(€)",
        "colTotal": "Gesamtpreis\n(€)",
        "grandTotal": "Gesamtpreis (EURO):",
        "priceNote": "Die obigen Preise sind in EURO angegeben und enthalten keine MwSt.",
        "conditionsTitle": "Allgemeine Bedingungen",
        "deliveryLabel": "Lieferzeit:",
        "deliveryWeeks": "Wochen",
        "notIncludeLabel": "Die Preise enthalten nicht:",
        "notInclude": [
            "Silogrundlagen, Dimensionierung der erforderlichen Versteifungen, Bau- und Mauerwerksarbeiten",
            "Arbeiten am Hauptstromanschluss",
            "Widerstands- und Isolationsmessungen",
            "Kosten bei der Inbetriebnahme und Probe (Materialien, Energie, Personal)",
            "Krankosten vor Ort (bei Außensilos: 2 Kräne/Tag, plus Kräne für die Entladung – 1 Kran)",
            "Zusatzkosten bei Verzögerungen, die vom Auftraggeber verursacht wurden, gehen zu Lasten des Auftraggebers",
        ],
        "warrantyLabel": "Garantie:",
        "warrantyText": "Die in diesem Angebot enthaltenen neuen Maschinen erhalten eine Garantie von 24 Monaten",
        "serviceText": "Für den Kundendienst nach der Garantie der in diesem Angebot enthaltenen Geräte wird ein Servicevertrag abgeschlossen",
        "paymentLabel": "Zahlungsbedingungen:",
        "payment1": "50% + MwSt. bei Vertragsunterzeichnung",
        "payment2": "40% + MwSt. nach Transport der Maschinen",
        "payment3": "10% + MwSt. nach Montage und Unterzeichnung des Abnahmeprotokolls",
        "validityLabel": "Gültigkeit des Angebots:",
        "validity21": "21 Tage ab Datum dieses Angebots",
        "before": "Vor der Auftragserteilung werden alle technischen Aspekte geklärt.",
        "contact": "Für Rückfragen oder weitere Informationen stehen wir Ihnen zur Verfügung.",
        "review": "Wir bitten Sie, uns nach der Analyse unseres Angebots zu informieren.",
        "regards": "Mit freundlichen Grüßen,",
        "installation": "Montagearbeiten",
        "installationSub": "Unterkunft, Personaltransport, usw.",
    },
    "en": {
        "offerFor": "OFFER FOR",
        "to": "To",
        "offerDate": "Offer date:",
        "regNo": "Reg. no.:",
        "intro": "Following your request, we have the pleasure of informing you of our price offer:",
        "colNo": "No.",
        "colName": "Description",
        "colQty": "Qty",
        "colUnit": "Unit price\n(€)",
        "colTotal": "Total price\n(€)",
        "grandTotal": "Total Price (EURO):",
        "priceNote": "Prices above are expressed in EURO and do not include VAT",
        "conditionsTitle": "General Terms",
        "deliveryLabel": "Delivery time:",
        "deliveryWeeks": "weeks",
        "notIncludeLabel": "Prices do not include:",
        "notInclude": [
            "silo foundations, sizing of reinforcements required for stabilization, construction and masonry work",
            "main electrical connection work",
            "resistance and insulation measurements",
            "expenses arising during commissioning and testing (materials, energy, personnel)",
            "crane costs at site (for exterior silos: 2 cranes/day, plus cranes needed for unloading – 1 crane)",
            "additional costs in case of delays caused by the client, these will be borne by the client",
        ],
        "warrantyLabel": "Warranty:",
        "warrantyText": "New equipment in this offer benefits from a 24-month warranty",
        "serviceText": "For post-warranty service of the equipment in this offer, a service contract will be drawn up",
        "paymentLabel": "Payment terms:",
        "payment1": "50% + VAT upon contract signing",
        "payment2": "40% + VAT after delivery of equipment",
        "payment3": "10% + VAT after installation and signing of the handover protocol",
        "validityLabel": "Offer validity:",
        "validity21": "21 days from the date of this offer",
        "before": "Before placing the order, all technical aspects will be clarified.",
        "contact": "For questions or additional information, we are at your disposal.",
        "review": "Please inform us after reviewing our offer.",
        "regards": "Yours sincerely,",
        "installation": "Installation labor",
        "installationSub": "Accommodation, personnel transport, etc.",
    },
}

_MONTHS = {
    "ro": ["ian.", "feb.", "mar.", "apr.", "mai", "iun.", "iul.", "aug.", "sep.", "oct.", "nov.", "dec."],
    "hu": ["jan.", "feb.", "már.", "ápr.", "máj.", "jún.", "júl.", "aug.", "szept.", "okt.", "nov.", "dec."],
    "de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def _esc(s: str) -> str:
    return html.escape(s or "")


def _fmt(n: float, lang: str) -> str:
    if lang == "en":
        return f"{n:,.2f}"
    # European style: 49.200,00
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _offer_number(quote_id: str, date: datetime) -> str:
    yr = str(date.year)[2:]
    mo = str(date.month).zfill(2)
    dy = str(date.day).zfill(2)
    digits = "".join(c for c in quote_id if c.isdigit())
    seq = digits[:3] if len(digits) >= 3 else digits.zfill(3)
    return f"S{yr}{mo}{dy}{seq or '001'}"


def _format_date(date: datetime, lang: str) -> str:
    month = _MONTHS[lang][date.month - 1]
    if lang == "hu":
        return f"{date.year}. {month} {date.day}."
    elif lang == "de":
        return f"{date.day}. {month} {date.year}"
    else:
        return f"{date.day} {month} {date.year}"


def generate_offer_html(
    quote: dict,
    company: dict | None,
    products: list[dict],
    lang: str,
    logo_data_uri: str | None,
    signature_data_uri: str | None,
) -> str:
    tr = T[lang]
    today = datetime.now()
    offer_no = _offer_number(quote["id"], today)
    date_str = _format_date(today, lang)
    client_name = company["name"] if company else ""

    items = quote.get("items") or []
    item_rows = []
    for idx, item in enumerate(items):
        product = next((p for p in products if p["id"] == item.get("productId")), None)
        product_name = product["name"] if product else item.get("productId", "")
        desc_map = product.get("description") or {} if product else {}
        lang_key = lang if lang in desc_map else "ro"
        product_desc = desc_map.get(lang_key, "")
        notes = item.get("notes", "")
        line_total = item.get("quantity", 0) * item.get("unitPrice", 0)

        sub_lines = ""
        if product_desc:
            sub_lines += f'<br/><span class="sub-desc">{_esc(product_desc)}</span>'
        if notes:
            sub_lines += f'<br/><span class="sub-desc">{_esc(notes)}</span>'

        item_rows.append(f"""
      <tr>
        <td class="cell-center cell-num">{idx + 1}</td>
        <td class="cell-description">
          <strong>{_esc(product_name)}</strong>{sub_lines}
        </td>
        <td class="cell-center">{item.get("quantity", 0)}</td>
        <td class="cell-right">{_fmt(item.get("unitPrice", 0), lang)}</td>
        <td class="cell-right">{_fmt(line_total, lang)}</td>
      </tr>""")

    installation = quote.get("installation") or 0.0
    if installation > 0:
        install_idx = len(items) + 1
        item_rows.append(f"""
      <tr>
        <td class="cell-center cell-num">{install_idx}</td>
        <td class="cell-description">
          <strong>{_esc(tr["installation"])}</strong>
          <br/><span class="sub-desc">{_esc(tr["installationSub"])}</span>
        </td>
        <td class="cell-center">1</td>
        <td class="cell-right">{_fmt(installation, lang)}</td>
        <td class="cell-right">{_fmt(installation, lang)}</td>
      </tr>""")

    grand_total = sum(i.get("quantity", 0) * i.get("unitPrice", 0) for i in items) + installation

    logo_img = (
        f'<img src="{logo_data_uri}" alt="SMS Reitler" />'
        if logo_data_uri
        else '<img src="/public/branding/sms-reitler.png" alt="SMS Reitler" />'
    )
    signature_img = (
        f'<img src="{signature_data_uri}" alt="Semnătură" style="max-height:80px; max-width:180px; display:block; margin-top:6pt;" />'
        if signature_data_uri
        else ""
    )

    exclusions_html = "\n        ".join(
        f"<li>{_esc(item)}</li>" for item in tr["notInclude"]
    )

    logo_tag = (
        f'<img src="{logo_data_uri}" alt="SMS Reitler" '
        f'style="max-width:190px; max-height:85px; object-fit:contain;" />'
        if logo_data_uri else ""
    )
    sig_tag = (
        f'<img src="{signature_data_uri}" alt="Semnătură" '
        f'style="max-height:90px; max-width:180px; display:block; margin-top:4pt;" />'
        if signature_data_uri else ""
    )

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8"/>
  <title>{_esc(tr["offerFor"])} {_esc(quote.get("name", ""))}</title>
  <style>
    @page {{
      size: A4;
      margin: 12mm 15mm 14mm 15mm;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: 10pt;
      color: #000;
    }}

    /* ── Company header ── */
    .header-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 5pt;
    }}
    .company-info {{
      font-size: 8.5pt;
      line-height: 1.6;
      vertical-align: top;
      width: 60%;
    }}
    .company-name {{
      font-weight: bold;
      font-size: 11pt;
      margin-bottom: 3pt;
    }}
    .logo-cell {{
      text-align: right;
      vertical-align: middle;
      width: 40%;
    }}

    hr {{ border: none; border-top: 1.5px solid #000; margin: 5pt 0; }}

    /* ── Offer meta (To / Date / RegNo) – use table, not flex ── */
    .meta-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 7pt 0 4pt;
    }}
    .meta-to {{
      font-size: 11pt;
      font-weight: bold;
      vertical-align: top;
    }}
    .meta-dates {{
      text-align: right;
      font-size: 9.5pt;
      line-height: 1.8;
      vertical-align: top;
      white-space: nowrap;
    }}
    .meta-dates b {{ font-weight: bold; }}

    .offer-title {{
      text-align: center;
      font-weight: bold;
      font-size: 12pt;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      margin: 9pt 0 5pt;
    }}
    .intro {{ font-size: 9.5pt; margin-bottom: 7pt; }}

    /* ── Items table ── */
    .items-table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      margin-bottom: 4pt;
    }}
    .items-table th {{
      background: #d9d9d9;
      border: 1px solid #000;
      padding: 4px 4px;
      font-size: 8.5pt;
      text-align: center;
      vertical-align: middle;
      font-weight: bold;
      white-space: pre-line;
    }}
    .items-table td {{
      border: 1px solid #000;
      padding: 3px 4px;
      font-size: 9pt;
      vertical-align: top;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }}
    .col-no   {{ width: 5%; }}
    .col-name {{ width: 55%; }}
    .col-qty  {{ width: 6%; }}
    .col-up   {{ width: 17%; }}
    .col-tot  {{ width: 17%; }}
    .cell-center {{ text-align: center; vertical-align: middle; }}
    .cell-right  {{ text-align: right;  vertical-align: middle; }}
    .sub-desc {{ font-size: 8.5pt; color: #333; }}
    .total-row td {{
      font-weight: bold;
      font-size: 11pt;
      background: #f0f0f0;
    }}

    .price-note {{
      font-weight: bold;
      font-size: 9.5pt;
      margin: 7pt 0 12pt;
    }}

    /* ── Conditions ── */
    .cond-title {{
      font-weight: bold;
      font-size: 12pt;
      text-align: center;
      text-decoration: underline;
      margin: 0 0 9pt;
    }}
    .cond-block {{ margin-bottom: 7pt; font-size: 9.5pt; line-height: 1.5; }}
    .cond-label {{ font-weight: bold; }}
    .excl-list {{ margin: 3pt 0 0 14pt; }}
    .excl-list li {{ margin-bottom: 2pt; }}
    .pay-indent {{ margin-left: 90pt; margin-top: 2pt; line-height: 1.8; }}

    /* ── Closing ── */
    .closing {{ margin-top: 18pt; font-size: 9.5pt; line-height: 1.7; }}
    .closing-notes {{ margin-bottom: 8pt; }}
    .sig-text {{ font-size: 10pt; line-height: 1.7; margin-top: 4pt; }}
  </style>
</head>
<body>

  <!-- Company header -->
  <table class="header-table">
    <tr>
      <td class="company-info">
        <div class="company-name">S.C. SMSS REITLER S.R.L.</div>
        <div>445100 Carei, jud. Satu Mare – RO, Calea Armatei Române, nr. 90</div>
        <div>Tel./Fax.: 00-40-261-863430, Mobil: 0744-520219</div>
        <div>CIF: RO15478578</div>
        <div>Nr. Reg. Com.: J30/427/2003</div>
        <div>Cont LEI: RO33BTRL03101202N12327XX</div>
        <div>Cont EUR: RO08BTRL03104202N12327XX</div>
        <div>Banca: Banca Transilvania, Agenția Carei</div>
        <div>E-mail: smsreitler@gmail.com</div>
        <div>Web: www.smsreitler.ro</div>
      </td>
      <td class="logo-cell">{logo_tag}</td>
    </tr>
  </table>

  <hr/>

  <!-- Client + date/reg -->
  <table class="meta-table">
    <tr>
      <td class="meta-to">{_esc(tr["to"])} <strong>{_esc(client_name)},</strong></td>
      <td class="meta-dates">
        <b>{_esc(tr["offerDate"])}</b> {_esc(date_str)}<br/>
        <b>{_esc(tr["regNo"])}</b> {_esc(offer_no)}
      </td>
    </tr>
  </table>

  <!-- Offer title -->
  <div class="offer-title">{_esc(tr["offerFor"])} {_esc(quote.get("name", ""))}</div>
  <div class="intro">{_esc(tr["intro"])}</div>

  <!-- Items table -->
  <table class="items-table">
    <colgroup>
      <col class="col-no"/>
      <col class="col-name"/>
      <col class="col-qty"/>
      <col class="col-up"/>
      <col class="col-tot"/>
    </colgroup>
    <thead>
      <tr>
        <th class="col-no">{_esc(tr["colNo"])}</th>
        <th class="col-name">{_esc(tr["colName"])}</th>
        <th class="col-qty">{_esc(tr["colQty"])}</th>
        <th class="col-up">{_esc(tr["colUnit"])}</th>
        <th class="col-tot">{_esc(tr["colTotal"])}</th>
      </tr>
    </thead>
    <tbody>
      {"".join(item_rows)}
      <tr class="total-row">
        <td colspan="3" style="text-align:right; padding-right:6px">
          {_esc(tr["grandTotal"])}
        </td>
        <td colspan="2" class="cell-right" style="font-size:12pt">
          {_fmt(grand_total, lang)}
        </td>
      </tr>
    </tbody>
  </table>

  <div class="price-note">{_esc(tr["priceNote"])}</div>

  <div class="cond-title">{_esc(tr["conditionsTitle"])}</div>

  <div class="cond-block">
    <span class="cond-label">{_esc(tr["deliveryLabel"])}</span>
    &nbsp;{quote.get("deliveryTimeWeeks", 4)} {_esc(tr["deliveryWeeks"])}
  </div>

  <div class="cond-block">
    <div class="cond-label">{_esc(tr["notIncludeLabel"])}</div>
    <ul class="excl-list">
      {exclusions_html}
    </ul>
  </div>

  <div class="cond-block">
    <span class="cond-label">{_esc(tr["warrantyLabel"])}</span>
    &nbsp;{_esc(tr["warrantyText"])}
  </div>

  <div class="cond-block">{_esc(tr["serviceText"])}</div>

  <div class="cond-block">
    <span class="cond-label">{_esc(tr["paymentLabel"])}</span>
    <div class="pay-indent">
      {_esc(tr["payment1"])}<br/>
      {_esc(tr["payment2"])}<br/>
      {_esc(tr["payment3"])}
    </div>
  </div>

  <div class="cond-block">
    <span class="cond-label">{_esc(tr["validityLabel"])}</span>
    &nbsp;<strong>{_esc(tr["validity21"])}</strong>
  </div>

  <div class="closing">
    <div class="closing-notes">
      {_esc(tr["before"])}<br/>
      {_esc(tr["contact"])}<br/>
      {_esc(tr["review"])}
    </div>
    <div class="sig-text">
      {_esc(tr["regards"])}<br/>
      {sig_tag}
      Alexandru Reitler
    </div>
  </div>

</body>
</html>"""


def generate_offer_pdf(
    quote: dict,
    company: dict | None,
    products: list[dict],
    lang: str,
    logo_data_uri: str | None,
    signature_data_uri: str | None,
) -> bytes:
    html_content = generate_offer_html(
        quote=quote,
        company=company,
        products=products,
        lang=lang,
        logo_data_uri=logo_data_uri,
        signature_data_uri=signature_data_uri,
    )
    return WeasyprintHTML(string=html_content).write_pdf()
