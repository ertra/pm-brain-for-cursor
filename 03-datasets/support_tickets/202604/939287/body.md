# iOS app crashes on save when editing a sequence

**Petra Novakova (Initech)** — 2026-04-22 10:40

Hello,

Several of our reps on iOS are reporting that the Cadenza mobile app
crashes whenever they try to **save edits to an existing sequence step**.
The pattern is consistent:

1. Open the mobile app.
2. Navigate to a sequence the rep owns.
3. Tap on any existing step.
4. Modify the subject or body text.
5. Tap "Save" — app crashes, returns to home screen.

Affected devices:

- iPhone 13, iOS 18.4
- iPhone 14 Pro, iOS 18.4
- iPad Air, iPadOS 18.4

We do not see this on Android (Samsung S24, Android 14) — works fine there.
About a third of our reps work primarily from mobile while on the road, so
this is blocking a real chunk of our team.

I attached the crash logs from TestFlight from two reps. Could you confirm
this is a known issue with iOS 18.4?

---

**Hannah Lee (Cadenza Support)** — 2026-04-22 16:18

Hi Petra, thanks for the detailed report and the crash logs. We have seen
two other tickets about this since iOS 18.4 shipped — looks related to a
change in how iOS handles the form view we use in the sequence editor.

Engineering is reproducing it now. As a workaround, reps can edit
sequences from the web app until the patched iOS build ships (estimated
within 1 week). I will update this ticket the moment the build is out.

---

**Petra Novakova (Initech)** — 2026-04-23 08:05

Thanks Hannah, that's helpful. I sent a note to our team to use the web
app in the meantime. Please ping me as soon as the mobile build lands.
