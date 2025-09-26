# app/routes/admin.py
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from .. import db
from ..models import OfficialMockExam, University, Faculty, User, Inquiry, FAQ, Reply

# 'admin'という名前で、URLの接頭辞が/adminのブループリントを作成
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理者確認用のデコレータ
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ここに、管理者関連の関数を全て移動してきます
# --- 管理者専用ルート ---

@admin_bp.route('/admin/exams')
@login_required
@admin_required
def admin_exams():
    exams = db.session.query(OfficialMockExam).order_by(OfficialMockExam.exam_date.desc()).all()
    return render_template('admin/admin_exams.html', exams=exams, user=current_user)

@admin_bp.route('/admin/exams/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_exam():
    if request.method == 'POST':
        # フォームからデータを受け取り、新しい模試を作成
        new_exam = OfficialMockExam(
            provider=request.form['provider'],
            name=request.form['name'],
            exam_date=date.fromisoformat(request.form['exam_date']),
            app_start_date=date.fromisoformat(request.form['app_start_date']),
            app_end_date=date.fromisoformat(request.form['app_end_date']),
            url=request.form['url']
        )
        db.session.add(new_exam)
        db.session.commit()
        return redirect(url_for('admin.admin_exams'))
    
    # ▼▼▼ GETリクエスト時にテンプレートを生成するロジックを追加 ▼▼▼
    provider = request.args.get('provider')
    exam_template = None
    if provider:
        provider_urls = {
            '河合塾': 'https://www.kawai-juku.ac.jp/moshi/',
            '駿台': 'https://www.sundai.ac.jp/moshi/',
            '東進': 'https://www.toshin-moshi.com/'
        }
        exam_template = OfficialMockExam(
            provider=provider,
            name=f"【{provider}】第X回 〇〇模試",
            url=provider_urls.get(provider, '')
        )
    return render_template('admin/admin_exam_form.html', user=current_user, exam=exam_template)


@admin_bp.route('/admin/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exam(exam_id):
    exam = db.session.query(OfficialMockExam).get_or_404(exam_id)
    if request.method == 'POST':
        # フォームからデータを受け取り、既存の模試を更新
        exam.provider = request.form['provider']
        exam.name = request.form['name']
        exam.exam_date = date.fromisoformat(request.form['exam_date'])
        exam.app_start_date = date.fromisoformat(request.form['app_start_date'])
        exam.app_end_date = date.fromisoformat(request.form['app_end_date'])
        exam.url = request.form['url']
        db.session.commit()
        return redirect(url_for('admin.admin_exams'))
    return render_template('admin/admin_exam_form.html', user=current_user, exam=exam)

@admin_bp.route('/admin/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exam(exam_id):
    exam = db.session.query(OfficialMockExam).get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    return redirect(url_for('admin.admin_exams'))

@admin_bp.route('/admin/universities')
@login_required
@admin_required
def admin_universities():
    universities = db.session.query(University).order_by(University.kana_name).all()
    return render_template('admin/admin_universities.html', universities=universities, user=current_user)

@admin_bp.route('/admin/universities/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_university():
    if request.method == 'POST':
        new_uni = University(
            name=request.form['name'],
            kana_name=request.form['kana_name'],
            level=request.form['level'],
            info_url=request.form['info_url']
        )
        db.session.add(new_uni)
        db.session.commit()
        flash('新しい大学を登録しました。')
        return redirect(url_for('admin.admin_universities'))
    return render_template('admin/admin_university_form.html', user=current_user, university=None)

@admin_bp.route('/admin/universities/<int:uni_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_university(uni_id):
    university = db.session.query(University).get_or_404(uni_id)
    if request.method == 'POST':
        university.name = request.form['name']
        university.kana_name = request.form['kana_name']
        university.level = request.form['level']
        university.info_url = request.form['info_url']
        db.session.commit()
        flash('大学情報を更新しました。')
        return redirect(url_for('admin.edit_university', uni_id=uni_id))
    
    # ▼▼▼ この大学に所属する学部リストを取得する処理を追加 ▼▼▼
    faculties = db.session.query(Faculty).filter_by(university_id=uni_id).order_by(Faculty.name).all()
    return render_template('admin/admin_university_form.html', user=current_user, university=university, faculties=faculties)

# ▼▼▼ 新しい学部を追加するためのルート ▼▼▼
@admin_bp.route('/admin/universities/<int:uni_id>/faculties/add', methods=['POST'])
@login_required
@admin_required
def add_faculty(uni_id):
    university = db.session.query(University).get_or_404(uni_id)
    faculty_name = request.form.get('faculty_name')
    if faculty_name:
        new_faculty = Faculty(university_id=university.id, name=faculty_name)
        db.session.add(new_faculty)
        db.session.commit()
        flash(f"学部「{faculty_name}」を追加しました。")
    return redirect(url_for('admin.edit_university', uni_id=uni_id))

# ▼▼▼ 学部を削除するためのルート ▼▼▼
@admin_bp.route('/admin/faculties/<int:faculty_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_faculty(faculty_id):
    faculty = db.session.query(Faculty).get_or_404(faculty_id)
    uni_id = faculty.university_id
    db.session.delete(faculty)
    db.session.commit()
    flash(f"学部「{faculty.name}」を削除しました。")
    return redirect(url_for('admin.edit_university', uni_id=uni_id))

@admin_bp.route('/admin/universities/<int:uni_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_university(uni_id):
    university = db.session.query(University).get_or_404(uni_id)
    # TODO: この大学に関連する学部も削除するロジックを追加すると、より丁寧です。
    db.session.delete(university)
    db.session.commit()
    flash('大学を削除しました。')
    return redirect(url_for('admin.admin_universities'))

@admin_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = db.session.query(User).order_by(User.id.desc()).all()
    user_count = len(users)
    return render_template('admin/admin_users.html', users=users, user_count=user_count, user=current_user)

@admin_bp.route('/admin/inquiries')
@login_required
@admin_required
def admin_inquiries():
    inquiries = db.session.query(Inquiry).order_by(Inquiry.created_at.desc()).all()
    return render_template('admin/admin_inquiries.html', inquiries=inquiries, user=current_user)

@admin_bp.route('/admin/inquiry/<int:inquiry_id>/faq', methods=['GET', 'POST'])
@login_required
@admin_required
def faq_from_inquiry(inquiry_id):
    inquiry = db.session.query(Inquiry).get_or_404(inquiry_id)
    
    if request.method == 'POST':
        # ▼▼▼ 編集された質問と回答の両方を取得 ▼▼▼
        question_text = request.form.get('question')
        answer_text = request.form.get('answer')

        if question_text and answer_text:
            new_faq = FAQ(
                question=question_text, # 編集された質問を使用
                answer=answer_text
            )
            db.session.add(new_faq)
            inquiry.is_resolved = True
            db.session.commit()
            inquiry.faq_id = new_faq.id
            db.session.commit()
            flash('FAQに登録し、お問い合わせを対応済みにしました。')
            return redirect(url_for('admin.admin_inquiries'))

    return render_template('admin/admin_faq_form_from_inquiry.html', inquiry=inquiry, user=current_user)

@admin_bp.route('/admin/inquiry/<int:inquiry_id>/reply', methods=['GET', 'POST'])
@login_required
@admin_required
def reply_to_inquiry(inquiry_id):
    inquiry = db.session.query(Inquiry).get_or_404(inquiry_id)
    if request.method == 'POST':
        reply_message = request.form.get('message')
        if reply_message:
            new_reply = Reply(
                inquiry_id=inquiry.id,
                admin_id=current_user.id,
                message=reply_message
            )
            db.session.add(new_reply)
            inquiry.is_resolved = True
            db.session.commit()
            flash('返信を送信し、お問い合わせを対応済みにしました。')
            return redirect(url_for('admin.admin_inquiries'))
            
    return render_template('admin/admin_reply_form.html', inquiry=inquiry, user=current_user)

# app/routes.py に追加

@admin_bp.route('/admin/faqs')
@login_required
@admin_required
def admin_faqs():
    faqs = db.session.query(FAQ).order_by(FAQ.sort_order).all()
    return render_template('admin/admin_faqs.html', faqs=faqs, user=current_user)

@admin_bp.route('/admin/faqs/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_faq():
    if request.method == 'POST':
        new_faq = FAQ(
            question=request.form['question'],
            answer=request.form['answer'],
            sort_order=int(request.form.get('sort_order', 0))
        )
        db.session.add(new_faq)
        db.session.commit()
        flash('新しいFAQを登録しました。')
        return redirect(url_for('admin.admin_faqs'))
    return render_template('admin/admin_faq_form.html', user=current_user, faq=None)

@admin_bp.route('/admin/faqs/<int:faq_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_faq(faq_id):
    faq = db.session.query(FAQ).get_or_404(faq_id)
    if request.method == 'POST':
        faq.question = request.form['question']
        faq.answer = request.form['answer']
        faq.sort_order = int(request.form.get('sort_order', 0))
        db.session.commit()
        flash('FAQを更新しました。')
        return redirect(url_for('admin.admin_faqs'))
    return render_template('admin/admin_faq_form.html', user=current_user, faq=faq)

@admin_bp.route('/admin/faqs/<int:faq_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_faq(faq_id):
    faq = db.session.query(FAQ).get_or_404(faq_id)
    
    # ▼▼▼ このブロックを追加 ▼▼▼
    # このFAQを参照している全てのお問い合わせを探す
    linked_inquiries = db.session.query(Inquiry).filter_by(faq_id=faq_id).all()
    for inquiry in linked_inquiries:
        # つながりを断ち切る (faq_idをNoneにする)
        inquiry.faq_id = None
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    
    db.session.delete(faq)
    db.session.commit()
    flash('FAQを削除しました。')
    return redirect(url_for('admin.admin_faqs'))

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    user_count = db.session.query(User).count()
    unresolved_inquiries = db.session.query(Inquiry).filter_by(is_resolved=False).count()
    return render_template(
        'admin/admin_dashboard.html', 
        user=current_user,
        user_count=user_count,
        unresolved_inquiries=unresolved_inquiries
    )