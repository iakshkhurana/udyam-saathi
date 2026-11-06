from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Order, OrderEvent, Quote
from .catalogue import get_catalogue
from .rules_engine import inr

STAGES = ["QUOTE_ACCEPTED", "CONSENT_GIVEN", "KYC_VERIFIED", "INSTALL_SCHEDULED", "INSTALLED", "ACTIVATED"]
STAGE_LABELS = {
    "QUOTE_ACCEPTED": ("Quote accepted", "कोटेशन स्वीकार"), "CONSENT_GIVEN": ("Consent given", "सहमति दी"),
    "KYC_VERIFIED": ("KYC verified", "KYC पूरा"), "KYC_REVIEW": ("KYC under review", "KYC जाँच में"),
    "INSTALL_SCHEDULED": ("Installation scheduled", "इंस्टॉलेशन तय"), "INSTALLED": ("Installed", "इंस्टॉल हो गया"),
    "ACTIVATED": ("Activated", "चालू"), "DELAYED": ("Delayed", "देरी"), "CANCELLED": ("Cancelled", "रद्द"),
}
TECHNICIANS = [("Ravi Kumar", "रवि कुमार"), ("Sunil Yadav", "सुनील यादव"), ("Imran Shaikh", "इमरान शेख"),
               ("Priya Nair", "प्रिया नायर")]
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_HI = ["सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "रवि"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
SLOT = ("10am and 1pm", "सुबह 10 से दोपहर 1 बजे")
DELAY_REASON = ("our fibre team needs one extra municipal permit for your street",
                "आपकी गली के लिए नगर निगम की एक अतिरिक्त अनुमति चाहिए")
DELAY_CREDIT = 100
DELAY_DAYS = 3


def fmt(d: date, lang: str = "en") -> str:
    if lang == "hi":
        return f"{DAYS_HI[d.weekday()]}, {d.day} {MONTHS_HI[d.month - 1]}"
    return f"{DAYS_EN[d.weekday()]} {d.day} {MONTHS_EN[d.month - 1]}"


def add_days_skip_sundays(start: date, days: int) -> date:
    d = start
    while days > 0:
        d += timedelta(days=1)
        if d.weekday() != 6:
            days -= 1
    return d


def technician(order: Order) -> tuple[str, str]:
    return TECHNICIANS[int(order.id, 16) % len(TECHNICIANS)]


def build_schedule(kyc_date: date, install_days: int, extra_days: int = 0) -> dict:
    install = add_days_skip_sundays(kyc_date, install_days + extra_days)
    return {"QUOTE_ACCEPTED": kyc_date.isoformat(), "CONSENT_GIVEN": kyc_date.isoformat(),
            "KYC_VERIFIED": kyc_date.isoformat(), "INSTALL_SCHEDULED": kyc_date.isoformat(),
            "INSTALLED": install.isoformat(), "ACTIVATED": (install + timedelta(days=1)).isoformat()}


def message(order: Order, status: str) -> tuple[str, str]:
    snap, sched = order.snapshot, order.schedule
    tech_en, tech_hi = technician(order)
    install = date.fromisoformat(sched["INSTALLED"]) if sched.get("INSTALLED") else None
    first_name_en, first_name_hi = tech_en.split()[0], tech_hi.split()[0]
    match status:
        case "QUOTE_ACCEPTED":
            return (f"Order {order.id} confirmed: {snap['bundle_name']} at {inr(snap['monthly_total'])}/month + GST. "
                    "Next: consent and KYC – it takes about 5 minutes.",
                    f"ऑर्डर {order.id} पक्का: {snap['bundle_name']}, {inr(snap['monthly_total'])}/महीना + GST। "
                    "अगला कदम: सहमति और KYC – लगभग 5 मिनट।")
        case "CONSENT_GIVEN":
            return ("Thanks for your consent. Upload your documents to finish KYC – no visit needed.",
                    "सहमति के लिए धन्यवाद। KYC पूरा करने के लिए दस्तावेज़ अपलोड करें – किसी विज़िट की ज़रूरत नहीं।")
        case "KYC_REVIEW":
            return ("Your documents are with our KYC team for a quick check. We'll update you by 6pm today.",
                    "आपके दस्तावेज़ हमारी KYC टीम देख रही है। आज शाम 6 बजे तक अपडेट देंगे।")
        case "KYC_VERIFIED":
            return ("KYC verified ✅ Your installation is being scheduled.",
                    "KYC पूरा ✅ आपका इंस्टॉलेशन तय किया जा रहा है।")
        case "INSTALL_SCHEDULED":
            return (f"Your technician {first_name_en} will visit on {fmt(install)} between {SLOT[0]}.",
                    f"आपके टेक्नीशियन {first_name_hi} {fmt(install, 'hi')} को {SLOT[1]} के बीच आएँगे।")
        case "INSTALLED":
            return ("Installation complete. Your services go live within 24 hours.",
                    "इंस्टॉलेशन पूरा। आपकी सेवाएँ 24 घंटे में चालू हो जाएँगी।")
        case "ACTIVATED":
            return (f"You're live! 🎉 Your first bill will be {inr(snap['monthly_total'])} + GST. "
                    "Refer a business – you both get 1 month of Biz Fibre free.",
                    f"आपकी सेवाएँ चालू! 🎉 पहला बिल {inr(snap['monthly_total'])} + GST होगा। "
                    "किसी बिज़नेस को रेफ़र करें – दोनों को 1 महीना Biz Fibre फ़्री।")
        case "DELAYED":
            return (f"Sorry – {DELAY_REASON[0]}. New installation date: {fmt(install)}. "
                    f"We've added a {inr(DELAY_CREDIT)} credit to your account. No need to call us – we'll keep you posted here.",
                    f"माफ़ कीजिए – {DELAY_REASON[1]}। नई तारीख: {fmt(install, 'hi')}। "
                    f"आपके खाते में {inr(DELAY_CREDIT)} क्रेडिट जोड़ दिया है। कॉल करने की ज़रूरत नहीं – हम यहीं अपडेट देंगे।")
        case "CANCELLED":
            return ("Your order was cancelled and your documents have been deleted.",
                    "आपका ऑर्डर रद्द हो गया और आपके दस्तावेज़ हटा दिए गए हैं।")
    raise ValueError(status)


def add_event(order: Order, status: str, on_date: date | None = None) -> None:
    en, hi = message(order, status)
    order.events.append(OrderEvent(status=status, on_date=on_date or get_settings().app_today,
                                   message_en=en, message_hi=hi))


def create_order(db: Session, q: Quote, view: dict) -> Order:
    cat = get_catalogue()
    install_days = max([1] + [cat[i["product_id"]].install_days for i in view["items"] if i["enabled"]])
    snapshot = {k: view[k] for k in ("bundle_name", "monthly_total", "setup_total", "contract_months", "language")}
    snapshot["items"] = [{k: i[k] for k in ("product_id", "name", "qty", "monthly")} for i in view["items"] if i["enabled"]]
    snapshot["install_days"] = install_days
    order = Order(quote_id=q.id, status="QUOTE_ACCEPTED", language=view["language"], snapshot=snapshot,
                  schedule=build_schedule(get_settings().app_today, install_days))
    db.add(order)
    db.flush()
    q.status = "accepted"
    add_event(order, "QUOTE_ACCEPTED")
    return order


def set_status(order: Order, status: str) -> None:
    today = get_settings().app_today
    if status in ("KYC_VERIFIED", "KYC_REVIEW") and order.status not in ("KYC_VERIFIED", "KYC_REVIEW"):
        order.schedule = build_schedule(today, order.snapshot["install_days"], DELAY_DAYS if order.delay else 0)
    order.status = status
    on = date.fromisoformat(order.schedule[status]) if status in order.schedule else today
    add_event(order, status, on)
    if status == "ACTIVATED":
        order.activated_on = on


def advance(order: Order) -> None:
    if order.cancelled or order.status == "ACTIVATED":
        raise ValueError("Order cannot advance")
    set_status(order, "KYC_VERIFIED" if order.status == "KYC_REVIEW" else STAGES[STAGES.index(order.status) + 1])


def delay(order: Order) -> None:
    if order.cancelled or order.status in ("INSTALLED", "ACTIVATED") or order.delay:
        raise ValueError("Order cannot be delayed now")
    kyc_date = date.fromisoformat(order.schedule["KYC_VERIFIED"])
    old = order.schedule["INSTALLED"]
    order.schedule = build_schedule(kyc_date, order.snapshot["install_days"], DELAY_DAYS)
    order.credit_inr += DELAY_CREDIT
    order.delay = {"reason_en": DELAY_REASON[0], "reason_hi": DELAY_REASON[1], "old_date": old,
                   "new_date": order.schedule["INSTALLED"], "credit_inr": DELAY_CREDIT}
    add_event(order, "DELAYED")


def cancel(order: Order) -> None:
    order.cancelled = True
    order.status = "CANCELLED"
    add_event(order, "CANCELLED")


def tracker_view(order: Order) -> dict:
    review = order.status == "KYC_REVIEW"
    idx = STAGES.index("CONSENT_GIVEN") if review else STAGES.index(order.status) if order.status in STAGES else -1
    tech_en, tech_hi = technician(order)
    stages = []
    for n, st in enumerate(STAGES):
        label = STAGE_LABELS["KYC_REVIEW" if review and st == "KYC_VERIFIED" else st]
        done_event = next((e for e in reversed(order.events) if e.status == st), None) if n <= idx else None
        stages.append({"status": st, "label_en": label[0], "label_hi": label[1],
                       "state": "done" if n <= idx else "current" if n == idx + 1 else "upcoming",
                       "date": done_event.on_date.isoformat() if done_event else order.schedule.get(st),
                       "expected": done_event is None})
    nxt = next((s for s in stages if s["state"] == "current"), None)
    return {
        "id": order.id, "status": order.status, "cancelled": order.cancelled, "language": order.language,
        "bundle_name": order.snapshot["bundle_name"], "monthly_total": order.snapshot["monthly_total"],
        "setup_total": order.snapshot["setup_total"], "contract_months": order.snapshot["contract_months"],
        "items": order.snapshot["items"], "progress": round(100 * (idx + 1) / len(STAGES)) if idx >= 0 else 0,
        "stages": stages, "next_update_by": f"{nxt['date']}T18:00" if nxt and nxt["date"] else None,
        "technician": {"name_en": tech_en, "name_hi": tech_hi, "phone_masked": "98•••••210", "rating": 4.8,
                       "slot_en": SLOT[0], "slot_hi": SLOT[1], "date": order.schedule.get("INSTALLED")},
        "delay": order.delay, "credit_inr": order.credit_inr, "nps": order.nps,
        "notifications": [{"status": e.status, "date": e.on_date.isoformat(), "message_en": e.message_en,
                           "message_hi": e.message_hi} for e in order.events],
    }
