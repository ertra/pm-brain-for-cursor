# Manager role cannot see reports for their direct team

**Carla Reyes (Nimbus Health)** — 2026-06-03 11:00

Hello,

We have a permissions issue that is blocking three of our regional sales
managers. Each manager has the **"Manager"** profile assigned (the
out-of-the-box one, no custom edits), and each has 5–8 direct reports
listed correctly under their account.

When the managers open the **Team Performance** dashboard, they see only
their own activity — none of their direct reports' data. If we
temporarily switch them to the **"Admin"** profile, all the data shows up
as expected; switching back to Manager hides it again.

This started after the platform update on 2026-05-30. Before that, the
Manager profile worked correctly for our team hierarchy.

For a healthcare-regulated environment we cannot leave managers on the
Admin role — that gives them way too much access to PHI fields. We need
the Manager role to work the way it did before the update.

---

**Olivier Bernard (Cadenza Support)** — 2026-06-03 15:42

Hi Carla, we identified the regression — the 2026-05-30 release tightened
the visibility rules on the Team Performance dashboard, and the
"direct-report inheritance" check is now stricter than before. Some
existing team hierarchies don't satisfy the new check.

A hotfix is being prepared for next Tuesday's release. As a temporary
workaround, you can create a **custom role** that mirrors Manager plus
the additional `team_reports_view` permission. I'm sending the exact
permission set in a follow-up DM.

---

**Carla Reyes (Nimbus Health)** — 2026-06-04 09:25

Workaround applied for our three regional managers, and they confirm
they can see their team's data again. We will revert to the
out-of-the-box Manager role once the hotfix ships next Tuesday. Thanks
for the quick turnaround.
