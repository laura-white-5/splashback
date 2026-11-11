"""SplashBack web app (Teacher web app + API layer, SIMPLIFIED)

The routes only call each module's interface, all the logic lives in the modules.
Run with:  python app.py   then open http://127.0.0.1:5000
"""
from flask import Flask, redirect, render_template, request, url_for

from access.service import AccessService
from ai_provider.factory import get_ai_provider
from ai_provider.mock import MockAIProvider
from notes.service import NotesService
from reports.service import ReportService
from review.service import ApprovalError, ReviewService
from roster.service import RosterService
from skills.service import SkillsService

LESSON_ID = "LESSON-1"   # Simplified: one lesson per class in the prototype


def create_app(db_path="splashback.db"):
    app = Flask(__name__)

    roster = RosterService()
    skills = SkillsService()
    access = AccessService(roster)
    notes = NotesService(db_path)
    review = ReviewService(db_path)

    def report_service(simulate_outage=False, simulate_mistake=False):
        # Demo switches let the teacher see how the app handles AI failure and AI mistakes
        if simulate_outage:
            ai = MockAIProvider(fail=True)
        elif simulate_mistake:
            ai = MockAIProvider(extra_claim="Just started inverted breaststroke")
        else:
            ai = get_ai_provider()
        return ReportService(roster, skills, notes, review, ai)

    def child_status(child_id):
        report = review.get_report(child_id, LESSON_ID)
        if report and report["status"] == "approved":
            return "Approved"
        if report:
            return "Draft ready"
        if notes.get_note(child_id, LESSON_ID):
            return "Notes saved"
        return "Notes needed"

    # Screen 1: My classes
    @app.route("/")
    def my_classes():
        user = access.current_user()
        classes = roster.get_classes_for_teacher(user["user_id"])
        return render_template("my_classes.html", user=user, classes=classes)

    # Screen 2: Class overview
    @app.route("/class/<class_id>")
    def class_overview(class_id):
        swim_class = roster.get_class(class_id)
        rows = [{"child": c, "statuses": skills.get_statuses(c.child_id),
                 "status": child_status(c.child_id)} for c in swim_class.children]
        return render_template("class_overview.html", swim_class=swim_class, rows=rows)

    # Screen 3: Add lesson notes (one child at a time)
    @app.route("/class/<class_id>/notes/<int:index>", methods=["GET", "POST"])
    def add_notes(class_id, index):
        swim_class = roster.get_class(class_id)
        children = swim_class.children
        child = children[index]
        error = None
        if request.method == "POST":
            try:
                notes.save_note(child.child_id, LESSON_ID, request.form["note"])
                if request.form.get("action") == "next" and index + 1 < len(children):
                    return redirect(url_for("add_notes", class_id=class_id, index=index + 1))
                return redirect(url_for("class_overview", class_id=class_id))
            except ValueError as e:
                error = str(e)
        note = notes.get_note(child.child_id, LESSON_ID)
        return render_template("add_notes.html", swim_class=swim_class, child=child,
                               index=index, total=len(children),
                               statuses=skills.get_statuses(child.child_id),
                               note=note.text if note else "", error=error)

    # Screen 4: Generate reports (or AI unavailable)
    @app.route("/class/<class_id>/generate", methods=["POST"])
    def generate(class_id):
        service = report_service(simulate_outage="outage" in request.form,
                                 simulate_mistake="mistake" in request.form)
        summary = service.request_reports(class_id, LESSON_ID)
        return render_template("generate_result.html", swim_class=roster.get_class(class_id),
                               summary=summary)

    # Screen 5: Review report
    @app.route("/class/<class_id>/review/<child_id>", methods=["GET", "POST"])
    def review_report(class_id, child_id):
        user = access.current_user()
        if not access.can_view(user["user_id"], child_id):
            return "Not allowed", 403
        report = review.get_report(child_id, LESSON_ID)
        if report is None:
            return redirect(url_for("class_overview", class_id=class_id))
        error = None

        if request.method == "POST":
            action = request.form["action"]
            if action == "remove":
                # Edit: remove one line, then re-run the safety check on the edited draft.
                draft = report["draft"]
                getattr(draft, request.form["section"]).pop(int(request.form["item"]))
                warnings = report_service().recheck(child_id, LESSON_ID, draft)
                review.update_draft(report["report_id"], draft, warnings)
            elif action == "approve":
                try:
                    review.approve(report["report_id"], user["user_id"])
                    return redirect(url_for("approved_report", class_id=class_id, child_id=child_id))
                except ApprovalError as e:
                    error = str(e)
            report = review.get_report(child_id, LESSON_ID)
        else:
            review.mark_opened(report["report_id"])   # teacher has now opened the report

        child = next(c for c in roster.get_class(class_id).children if c.child_id == child_id)
        return render_template("review_report.html", class_id=class_id, child=child,
                               report=report, note=notes.get_note(child_id, LESSON_ID),
                               statuses=skills.get_statuses(child_id), error=error)

    # Screen 6: Approved report (what the parent sees)
    @app.route("/class/<class_id>/approved/<child_id>")
    def approved_report(class_id, child_id):
        report = review.get_report(child_id, LESSON_ID)
        if report is None or not review.is_shareable(report["report_id"]):
            return redirect(url_for("review_report", class_id=class_id, child_id=child_id))
        swim_class = roster.get_class(class_id)
        child = next(c for c in swim_class.children if c.child_id == child_id)
        return render_template("approved_report.html", class_id=class_id, child=child,
                               level=swim_class.level, report=report,
                               teacher=access.current_user()["name"])

    return app


if __name__ == "__main__":
    create_app().run(debug=True)