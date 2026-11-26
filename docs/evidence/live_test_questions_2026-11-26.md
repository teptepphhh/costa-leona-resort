# Live test questions, local stack, 2026-11-26 (gemini-3.5-flash-lite, outputs copied as returned)

T1 (works)  Q: How much would 3 nights in a Seaview Room cost in total, with early check-in?
   A: Seaview Room is PHP 5,800 per night, so 3 nights would be PHP 17,400. Early check-in from 10:00 AM is available for PHP 1,000, subject to room readiness. ...
   Verdict: correct (3 x 5,800 = 17,400; early check-in 1,000). It did not add the total (18,400) but gave both correct parts.

T2 (works)  Q: Mura ba ang Garden Room kaysa Seaview Room? Magkano ang pagkakaiba?
   A: Opo, mas mura po ang Garden Room ... PHP 4,200 ... PHP 5,800 ... pagkakaiba po ay PHP 1,600 bawat gabi.
   Verdict: correct, answered in Filipino.

T3 (FAILS) Q: We are 2 adults and 2 children aged 7 and 9. Which room should we book and how much per night?
   A: ... the Lioness Family Villa is the best choice. It accommodates up to 4 adults and 1 child ... PHP 9,500 per night ...
   Verdict: WRONG/unsafe. The knowledge base says the villa fits 4 adults + 1 child. Two children is over the stated child limit, but Leona recommended it without flagging the problem and without asking the front desk to confirm.

Other observation  Q: Is the resort open on Christmas Day and do you have a Christmas dinner?
   A: Our front desk is open 24 hours every day, so the resort is open on Christmas Day! ...
   Verdict: over-inference. The knowledge base never says the resort is open on Christmas Day; Leona inferred it from the 24-hour front desk.
