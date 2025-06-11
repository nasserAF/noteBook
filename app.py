from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import json
import datetime
import traceback
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore
from google.api_core import exceptions as google_exceptions

# إنشاء تطبيق يلا تاسكات
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

# Initialize Firebase
try:
    print("Attempting to initialize Firebase...")
    firebase_key_json = os.environ.get('firebase-key')
    if firebase_key_json:
        print("Found firebase-key environment variable. Initializing from env var.")
        cred_json = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_json)
    else:
        # Fallback to local file for local development
        print("firebase-key environment variable not found. Falling back to local firebase-key.json file.")
        cred = credentials.Certificate("firebase-key.json")
    print("Credentials loaded successfully")
    firebase_admin.initialize_app(cred, {
        'projectId': 'notebook-25b3d',
        'storageBucket': 'notebook-25b3d.firebasestorage.app'
    })
    print("Firebase app initialized")
    db = firestore.client()
    print("Firestore client created successfully")
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    print(traceback.format_exc())
    db = None
    
    # Create mock data for demonstration
    mock_todos = [
        {
            'id': '1',
            'title': 'إكمال المشروع',
            'details': 'إنهاء تطوير تطبيق يلا تاسكات والملاحظات',
            'priority': 'high',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'completed': False
        },
        {
            'id': '2',
            'title': 'قراءة كتاب',
            'details': 'قراءة كتاب عن تطوير الويب',
            'priority': 'medium',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'completed': True
        }
    ]
    
    mock_notes = [
        {
            'id': '1',
            'title': 'فكرة لمشروع جديد',
            'details': 'تطبيق للتعلم الذاتي باستخدام الذكاء الاصطناعي',
            'tags': ['تطوير', 'ذكاء اصطناعي', 'تعليم'],
            'links': ['https://example.com'],
            'images': [],
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': '2',
            'title': 'ملاحظات اجتماع',
            'details': 'مناقشة خطة العمل للربع القادم',
            'tags': ['عمل', 'اجتماع'],
            'links': [],
            'images': [],
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
    ]

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos')
def todos():
    note_id = request.args.get('note_id') # Get note_id from query params
    prefill_data = None

    if note_id and db:
        note_ref = db.collection('notes').document(note_id)
        note_data = note_ref.get().to_dict()
        if note_data:
            prefill_data = {
                'title': f"مهمة من ملاحظة: {note_data.get('title', '')}",
                'details': note_data.get('details', '')
            }
    elif note_id: # Handle demo mode if note_id is passed
        mock_note = next((n for n in mock_notes if n['id'] == note_id), None)
        if mock_note:
            prefill_data = {
                'title': f"مهمة من ملاحظة: {mock_note.get('title', '')}",
                'details': mock_note.get('details', '')
            }

    # Get todos from Firestore
    if db:
        todos_ref = db.collection('todos')
        todos = [doc.to_dict() for doc in todos_ref.stream()]
        for todo in todos:
            if 'date' in todo and isinstance(todo['date'], datetime.datetime):
                todo['date'] = todo['date'].strftime('%Y-%m-%d')
    else:
        # Use mock data in demo mode
        todos = mock_todos
    
    return render_template('todos.html', todos=todos, prefill_data=prefill_data) # Pass prefill_data

@app.route('/add_todo', methods=['POST']) # Keep only POST for adding
def add_todo():
    if request.method == 'POST':
        title = request.form.get('title')
        details = request.form.get('details')
        priority = request.form.get('priority')
        date = datetime.datetime.now()
        
        if db:
            todo_ref = db.collection('todos').document()
            todo_ref.set({
                'id': todo_ref.id,
                'title': title,
                'details': details,
                'priority': priority,
                'date': date,
                'completed': False
            })
            flash('Todo added successfully!', 'success')
        else:
            flash('Database connection error', 'error')
            
    return redirect(url_for('todos'))

@app.route('/update_todo/<todo_id>', methods=['POST'])
def update_todo(todo_id):
    if request.method == 'POST':
        title = request.form.get('title')
        details = request.form.get('details')
        priority = request.form.get('priority')
        
        if db:
            todo_ref = db.collection('todos').document(todo_id)
            todo_ref.update({
                'title': title,
                'details': details,
                'priority': priority
            })
            flash('Todo updated successfully!', 'success')
        else:
            flash('Database connection error', 'error')
            
    return redirect(url_for('todos'))

@app.route('/complete_todo/<todo_id>')
def complete_todo(todo_id):
    if db:
        todo_ref = db.collection('todos').document(todo_id)
        todo_ref.update({
            'completed': True
        })
        flash('Todo marked as completed!', 'success')
    else:
        flash('Database connection error', 'error')
        
    return redirect(url_for('todos'))

@app.route('/delete_todo/<todo_id>')
def delete_todo(todo_id):
    if db:
        todo_ref = db.collection('todos').document(todo_id)
        todo_ref.delete()
        flash('Todo deleted successfully!', 'success')
    else:
        flash('Database connection error', 'error')
        
    return redirect(url_for('todos'))

@app.route('/notes')
def notes():
    # Get *unarchived* notes from Firestore
    notes = []
    if db:
        notes_ref = db.collection('notes').where('archived', '==', False).order_by('date', direction=firestore.Query.DESCENDING)
        notes_stream = notes_ref.stream()
        
        notes = []
        for doc in notes_stream:
            note_data = doc.to_dict()
            note_data['id'] = doc.id # Add the document ID to the dictionary
            # Explicitly filter out archived notes if the where clause wasn't sufficient (e.g., field missing)
            if not note_data.get('archived', False): 
                if 'date' in note_data and isinstance(note_data['date'], datetime.datetime):
                    note_data['date'] = note_data['date'].strftime('%Y-%m-%d %H:%M')
                elif 'date' in note_data: # Handle potential string dates from mock data
                    try:
                       dt_obj = datetime.datetime.fromisoformat(str(note_data['date']).replace('Z', '+00:00'))
                       note_data['date'] = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                       pass # Keep original string if parsing fails
                notes.append(note_data)
    else:
        # Use mock data in demo mode (filter mock data too)
        notes = [note for note in mock_notes if not note.get('archived', False)]
    
    return render_template('notes.html', notes=notes)

@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form.get('title')
        details = request.form.get('details')
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        links = request.form.get('links', '').split(',')
        links = [link.strip() for link in links if link.strip()]
        date = datetime.datetime.now()
        
        # Handle multiple file uploads
        uploaded_files = request.files.getlist('attachments') # Changed from 'images'
        attachments_list = []
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename to avoid overwrites
                unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                file_url = url_for('static', filename=f'uploads/{unique_filename}')
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                file_type = 'image' if file_ext in {'png', 'jpg', 'jpeg', 'gif'} else 'file' # Basic type categorization
                attachments_list.append({'url': file_url, 'filename': filename, 'type': file_type})

        # Prepare note data
        note_data = {
            'id': '',
            'title': title,
            'details': details,
            'links': links,
            'tags': tags,
            'date': firestore.SERVER_TIMESTAMP, # Use server timestamp
            'attachments': attachments_list, # Changed from 'images'
            'archived': False
        }
            
        if db:
            note_ref = db.collection('notes').document()
            note_ref.set(note_data)
            flash('Note added successfully!', 'success')
            return redirect(url_for('notes'))
        else:
            flash('Database connection error', 'error')
    
    return render_template('add_note.html')

@app.route('/view_note/<note_id>')
def view_note(note_id):
    if db:
        note_ref = db.collection('notes').document(note_id)
        note = note_ref.get().to_dict()
        if note:
            note['id'] = note_id
            if 'date' in note and isinstance(note['date'], datetime.datetime):
                note['date'] = note['date'].strftime('%Y-%m-%d %H:%M')
            elif 'date' in note: # Handle potential string dates
                try:
                    dt_obj = datetime.datetime.fromisoformat(str(note['date']).replace('Z', '+00:00'))
                    note['date'] = dt_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    pass # Keep original string if parsing fails
            return render_template('view_note.html', note=note)
        else:
            flash('Note not found.', 'error')
            return redirect(url_for('notes'))
    else:
        flash('Database connection error', 'error')
        return redirect(url_for('notes'))
        
@app.route('/print_note/<note_id>')
def print_note(note_id):
    if db:
        note_ref = db.collection('notes').document(note_id)
        note = note_ref.get().to_dict()
        if note:
            note['id'] = note_id
            if 'date' in note and isinstance(note['date'], datetime.datetime):
                note['date'] = note['date'].strftime('%Y-%m-%d %H:%M')
            elif 'date' in note: # Handle potential string dates
                try:
                    dt_obj = datetime.datetime.fromisoformat(str(note['date']).replace('Z', '+00:00'))
                    note['date'] = dt_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    pass # Keep original string if parsing fails
            # Add current time for the footer
            now = datetime.datetime.now()
            return render_template('print_note.html', note=note, now=now)
        else:
            flash('Note not found.', 'error')
            return redirect(url_for('notes'))
    else:
        # Use mock data for demo mode
        mock_note = next((n for n in mock_notes if n['id'] == note_id), None)
        if mock_note:
            now = datetime.datetime.now()
            return render_template('print_note.html', note=mock_note, now=now)
        else:
            flash('Note not found in demo mode.', 'error')
            return redirect(url_for('notes'))

@app.route('/edit_note/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note_ref = db.collection('notes').document(note_id)
    note = note_ref.get().to_dict()

    if note is None:
        flash('Note not found.', 'error')
        return redirect(url_for('notes'))

    if request.method == 'POST':
        # Handle multiple file uploads
        uploaded_files = request.files.getlist('attachments') # Changed from 'images'
        # Start with existing attachments
        attachments_list = note.get('attachments', []) 

        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename
                unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                file_url = url_for('static', filename=f'uploads/{unique_filename}')
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                file_type = 'image' if file_ext in {'png', 'jpg', 'jpeg', 'gif'} else 'file'
                attachments_list.append({'url': file_url, 'filename': filename, 'type': file_type})
                
        # Process links and tags
        links = [link.strip() for link in request.form.get('links', '').split(',') if link.strip()]
        tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
        
        # Update note data
        note_ref.update({
            'title': request.form['title'],
            'details': request.form['details'],
            'links': links,
            'tags': tags,
            'date': firestore.SERVER_TIMESTAMP, # Update timestamp on edit
            'attachments': attachments_list, # Update attachments list
            'cover_image_url': request.form.get('cover_image_url') # Add cover_image_url
        })
        flash('Note updated successfully!', 'success')
        return redirect(url_for('view_note', note_id=note_id))

    # Ensure attachments is a list for the template, even if missing in older notes
    if 'attachments' not in note:
        note['attachments'] = []
        
    # Ensure cover_image_url is present for the template
    if 'cover_image_url' not in note:
        note['cover_image_url'] = None # Or set a default if preferred
        
    # Format date for display if it's a datetime object
    if 'date' in note and isinstance(note['date'], datetime.datetime):
        note['date_str'] = note['date'].strftime('%Y-%m-%d %H:%M')
    
    # Pass the note ID needed for deletion links
    note['id'] = note_id 

    return render_template('edit_note.html', note=note)

# Route to delete an *attachment* (Needs specific UI trigger)
@app.route('/delete_attachment/<note_id>/<path:attachment_url>')
def delete_attachment(note_id, attachment_url):
    if not db:
        flash("Database not connected.", "error")
        return redirect(request.referrer or url_for('notes'))

    note_ref = db.collection('notes').document(note_id)
    note = note_ref.get().to_dict()

    if not note:
        flash("Note not found.", "error")
        return redirect(url_for('notes'))

    original_attachments = note.get('attachments', [])
    updated_attachments = [att for att in original_attachments if att.get('url') != attachment_url]

    if len(original_attachments) == len(updated_attachments):
        flash("Attachment not found in note.", "warning")
    else:
        # Attempt to delete the actual file from static/uploads
        try:
            # Extract filename from URL (handle potential url_for generation)
            filename_to_delete = attachment_url.split('/')[-1] # Simple split, might need refinement
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted file: {filepath}")
            else:
                print(f"File not found for deletion: {filepath}")
        except Exception as e:
            print(f"Error deleting attachment file {attachment_url}: {e}")
            # Continue even if file deletion fails, just remove the reference

        note_ref.update({'attachments': updated_attachments})
        flash("Attachment deleted successfully.", "success")

    # Redirect back to the edit page usually makes sense
    return redirect(url_for('edit_note', note_id=note_id))

@app.route('/delete_note/<note_id>')
def delete_note(note_id):
    if db:
        note_ref = db.collection('notes').document(note_id)
        note_data = note_ref.get().to_dict()
        if note_data and 'attachments' in note_data:
            for attachment in note_data['attachments']:
                try:
                    # Assuming attachment['url'] is like /static/uploads/filename.jpg
                    filename = os.path.basename(attachment['url'])
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting image file {attachment['url']}: {e}")

        note_ref.delete()
        flash('Note deleted successfully!', 'success')
    else:
        # Handle deletion in demo mode if necessary
        global mock_notes
        mock_notes = [note for note in mock_notes if note['id'] != note_id]
        flash('Note deleted successfully (demo mode)!', 'success')

    return redirect(url_for('notes'))

@app.route('/archive_note/<note_id>')
def archive_note(note_id):
    if db:
        try:
            note_ref = db.collection('notes').document(note_id)
            note_ref.update({'archived': True})
            flash('تم أرشفة الملاحظة بنجاح!', 'success')
        except Exception as e:
            flash(f'حدث خطأ أثناء الأرشفة: {e}', 'error')
    else:
        # Demo mode handling
        global mock_notes
        for note in mock_notes:
            if note['id'] == note_id:
                note['archived'] = True
                flash('تم أرشفة الملاحظة بنجاح (وضع العرض)!', 'success')
                break
        else:
             flash('لم يتم العثور على الملاحظة (وضع العرض)', 'warning')
            
    # Redirect back to the main notes page
    return redirect(url_for('notes'))

@app.route('/unarchive_note/<note_id>')
def unarchive_note(note_id):
    if db:
        try:
            note_ref = db.collection('notes').document(note_id)
            note_ref.update({'archived': False})
            flash('تم استعادة الملاحظة بنجاح!', 'success')
        except Exception as e:
            flash(f'حدث خطأ أثناء استعادة الأرشيف: {e}', 'error')
    else:
        # Demo mode handling
        global mock_notes
        for note in mock_notes:
            if note['id'] == note_id:
                note['archived'] = False
                flash('تم استعادة الملاحظة بنجاح (وضع العرض)!', 'success')
                break
        else:
             flash('لم يتم العثور على الملاحظة (وضع العرض)', 'warning')
            
    # Redirect back to the archived notes page
    return redirect(url_for('archived_notes'))

@app.route('/archived_notes')
def archived_notes():
    # Get *archived* notes from Firestore
    archived_notes_list = []
    if db:
        notes_ref = db.collection('notes').where('archived', '==', True).order_by('date', direction=firestore.Query.DESCENDING)
        notes_stream = notes_ref.stream()
        
        archived_notes_list = []
        for doc in notes_stream:
                note_data = doc.to_dict()
                note_data['id'] = doc.id # Add the document ID to the dictionary
                if 'date' in note_data and isinstance(note_data['date'], datetime.datetime):
                    note_data['date'] = note_data['date'].strftime('%Y-%m-%d %H:%M')
                elif 'date' in note_data: 
                    try:
                        dt_obj = datetime.datetime.fromisoformat(str(note_data['date']).replace('Z', '+00:00'))
                        note_data['date'] = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        pass 
                archived_notes_list.append(note_data)
    else:
        # Use mock data in demo mode
        archived_notes_list = [note for note in mock_notes if note.get('archived', False)]

    return render_template('archived_notes.html', notes=archived_notes_list)

@app.route('/search_results')
def search_results():
    query = request.args.get('query', '').strip()
    print(f"Search query received: {query}") # For debugging

    # Basic placeholder: In a real implementation, you'd query Firestore 
    # for both todos and notes based on the 'query'
    # For now, just pass the query to the template
    found_todos = []
    found_notes = []

    if not query:
        flash("الرجاء إدخال كلمة للبحث", "warning")
        # Decide where to redirect if query is empty - maybe back to index?
        return redirect(request.referrer or url_for('index')) 

    if db: 
        try:
            # Simple search in todo titles/details (case-insensitive)
            todos_ref = db.collection('todos')
            all_todos = [doc.to_dict() for doc in todos_ref.stream()]
            found_todos = [t for t in all_todos if query.lower() in t.get('title', '').lower() or query.lower() in t.get('details', '').lower()]

            # Simple search in note titles/details/tags (case-insensitive)
            notes_ref = db.collection('notes').where('archived', '==', False) # Only search active notes
            all_notes = [doc.to_dict() for doc in notes_ref.stream()]
            found_notes = [n for n in all_notes if 
                           query.lower() in n.get('title', '').lower() or 
                           query.lower() in n.get('details', '').lower() or 
                           any(query.lower() in tag.lower() for tag in n.get('tags', []))]

        except google_exceptions.RetryError as e:
            flash(f"حدث خطأ أثناء الاتصال بقاعدة البيانات: {e}", "error")
            print(f"Firestore RetryError during search: {e}")
        except Exception as e:
            flash(f"حدث خطأ غير متوقع أثناء البحث: {e}", "error")
            print(f"Unexpected error during search: {e}\n{traceback.format_exc()}")
    else:
        # Basic mock search for demo mode
        found_todos = [t for t in mock_todos if query.lower() in t.get('title', '').lower() or query.lower() in t.get('details', '').lower()]
        found_notes = [n for n in mock_notes if 
                       query.lower() in n.get('title', '').lower() or 
                       query.lower() in n.get('details', '').lower() or 
                       any(query.lower() in tag.lower() for tag in n.get('tags', []))]
        if not found_todos and not found_notes:
            flash("لا توجد نتائج بحث مطابقة (وضع العرض)", "info")
        
    # Render a results template (needs to be created)
    return render_template('search_results.html', query=query, todos=found_todos, notes=found_notes)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = {'todos': [], 'notes': []}
    
    if db and query:
        # Search todos
        todos_ref = db.collection('todos')
        todos = [doc.to_dict() for doc in todos_ref.stream()]
        for todo in todos:
            if (query in todo.get('title', '').lower() or 
                query in todo.get('details', '').lower()):
                if 'date' in todo and isinstance(todo['date'], datetime.datetime):
                    todo['date'] = todo['date'].strftime('%Y-%m-%d')
                results['todos'].append(todo)
        
        # Search notes
        notes_ref = db.collection('notes')
        notes = [doc.to_dict() for doc in notes_ref.stream()]
        for note in notes:
            if (query in note.get('title', '').lower() or 
                query in note.get('details', '').lower() or
                any(query in tag.lower() for tag in note.get('tags', []))):
                if 'date' in note and isinstance(note['date'], datetime.datetime):
                    note['date'] = note['date'].strftime('%Y-%m-%d')
                results['notes'].append(note)
    elif query:
        # Search in mock data for demo mode
        for todo in mock_todos:
            if (query in todo.get('title', '').lower() or 
                query in todo.get('details', '').lower()):
                results['todos'].append(todo)
        
        for note in mock_notes:
            if (query in note.get('title', '').lower() or 
                query in note.get('details', '').lower() or
                any(query in tag.lower() for tag in note.get('tags', []))):
                results['notes'].append(note)
    
    return render_template('search_results.html', results=results, query=query)

# Blog Routes
@app.route('/blogs')
def blogs():
    try:
        if db:
            blogs_ref = db.collection('blogs')
            blogs = [{'id': doc.id, **doc.to_dict()} for doc in blogs_ref.stream()]
        else:
            blogs = []
        return render_template('blogs.html', blogs=blogs)
    except Exception as e:
        print(f"Error fetching blogs: {str(e)}")
        flash('حدث خطأ أثناء جلب المدونات', 'error')
        return render_template('blogs.html', blogs=[])

@app.route('/blogs/add', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'POST':
        try:
            blog_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if db:
                db.collection('blogs').add(blog_data)
                flash('تمت إضافة المدونة بنجاح', 'success')
                return redirect(url_for('blogs'))
        except Exception as e:
            print(f"Error adding blog: {str(e)}")
            flash('حدث خطأ أثناء إضافة المدونة', 'error')
    
    return render_template('blog_form.html', blog=None)

@app.route('/blogs/<blog_id>/edit', methods=['GET', 'POST'])
def edit_blog(blog_id):
    if request.method == 'POST':
        try:
            blog_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if db:
                db.collection('blogs').document(blog_id).update(blog_data)
                flash('تم تحديث المدونة بنجاح', 'success')
                return redirect(url_for('view_blog', blog_id=blog_id))
        except Exception as e:
            print(f"Error updating blog: {str(e)}")
            flash('حدث خطأ أثناء تحديث المدونة', 'error')
    
    try:
        if db:
            blog_ref = db.collection('blogs').document(blog_id)
            blog = blog_ref.get()
            if blog.exists:
                return render_template('blog_form.html', blog={'id': blog.id, **blog.to_dict()})
        
        flash('المدونة غير موجودة', 'error')
        return redirect(url_for('blogs'))
    except Exception as e:
        print(f"Error loading blog: {str(e)}")
        flash('حدث خطأ أثناء تحميل المدونة', 'error')
        return redirect(url_for('blogs'))

@app.route('/blogs/<blog_id>/delete', methods=['POST'])
def delete_blog(blog_id):
    try:
        if db:
            # First, delete all articles in this blog
            articles_ref = db.collection('blogs').document(blog_id).collection('articles')
            for article in articles_ref.stream():
                article.reference.delete()
            
            # Then delete the blog
            db.collection('blogs').document(blog_id).delete()
            flash('تم حذف المدونة وجميع مقالاتها بنجاح', 'success')
        else:
            flash('حدث خطأ أثناء حذف المدونة', 'error')
    except Exception as e:
        print(f"Error deleting blog: {str(e)}")
        flash('حدث خطأ أثناء حذف المدونة', 'error')
    return redirect(url_for('blogs'))

# Articles Routes
@app.route('/blogs/<blog_id>/articles')
def view_blog(blog_id):
    try:
        if not db:
            raise Exception("Database not available")
            
        blog_ref = db.collection('blogs').document(blog_id)
        blog = blog_ref.get()
        
        if not blog.exists:
            flash('المدونة غير موجودة', 'error')
            return redirect(url_for('blogs'))
            
        articles_ref = blog_ref.collection('articles')
        articles = [{'id': doc.id, **doc.to_dict()} for doc in articles_ref.stream()]
        
        return render_template('articles.html', 
                             blog={'id': blog.id, **blog.to_dict()}, 
                             articles=articles)
    except Exception as e:
        print(f"Error viewing blog: {str(e)}")
        flash('حدث خطأ أثناء تحميل المدونة', 'error')
        return redirect(url_for('blogs'))

@app.route('/blogs/<blog_id>/articles/add', methods=['GET', 'POST'])
def add_article(blog_id):
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            if not title:
                flash('عنوان المقالة مطلوب', 'error')
                return redirect(request.referrer)

            suggested_content_raw = request.form.get('suggested_content', '')
            # Use the unique separator from the frontend JavaScript
            suggested_content_list = [s.strip() for s in suggested_content_raw.split('|||---|||') if s.strip()]

            article_data = {
                'title': title,
                'final_content': request.form.get('final_content', ''),
                'suggested_content': suggested_content_list,
                'featured_image': request.form.get('featured_image', ''),
                'keywords': [k.strip() for k in request.form.get('keywords', '').split(',') if k.strip()],
                'sub_keywords': [sk.strip() for sk in request.form.get('sub_keywords', '').split(',') if sk.strip()],
                'tags': [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()],
                'meta_descriptions': [m.strip() for m in request.form.get('meta_descriptions', '').split('\n') if m.strip()],
                'permalinks': [p.strip() for p in request.form.get('permalinks', '').split('\n') if p.strip()],
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if db:
                db.collection('blogs').document(blog_id).collection('articles').add(article_data)
                flash('تمت إضافة المقالة بنجاح', 'success')
                return redirect(url_for('view_blog', blog_id=blog_id))
        except Exception as e:
            print(f"Error adding article: {str(e)}")
            flash('حدث خطأ أثناء إضافة المقالة', 'error')
    
    return render_template('article_form.html', blog_id=blog_id, article=None, blog={'id': blog_id})

@app.route('/blogs/<blog_id>/articles/<article_id>/edit', methods=['GET', 'POST'])
def edit_article(blog_id, article_id):
    if request.method == 'POST':
        try:
            if not db:
                flash('خطأ في الاتصال بقاعدة البيانات', 'error')
                return redirect(url_for('view_blog', blog_id=blog_id))
                
            title = request.form.get('title')
            if not title:
                flash('عنوان المقالة مطلوب', 'error')
                return redirect(request.referrer)
                
            suggested_content_raw = request.form.get('suggested_content', '')
            # Use the unique separator from the frontend JavaScript
            suggested_content_list = [s.strip() for s in suggested_content_raw.split('|||---|||') if s.strip()]

            article_data = {
                'title': title,
                'final_content': request.form.get('final_content', ''),
                'suggested_content': suggested_content_list,
                'featured_image': request.form.get('featured_image', ''),
                'keywords': [k.strip() for k in request.form.get('keywords', '').split(',') if k.strip()],
                'sub_keywords': [sk.strip() for sk in request.form.get('sub_keywords', '').split(',') if sk.strip()],
                'tags': [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()],
                'meta_descriptions': [m.strip() for m in request.form.get('meta_descriptions', '').split('\n') if m.strip()],
                'permalinks': [p.strip() for p in request.form.get('permalinks', '').split('\n') if p.strip()],
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            article_ref = db.collection('blogs').document(blog_id).collection('articles').document(article_id)
            article_ref.update(article_data)
            
            flash('تم تحديث المقالة بنجاح', 'success')
            return redirect(url_for('view_blog', blog_id=blog_id))
            
        except Exception as e:
            print(f"Error updating article: {str(e)}")
            flash(f'حدث خطأ أثناء تحديث المقالة: {str(e)}', 'error')
            return redirect(url_for('view_blog', blog_id=blog_id))
        except Exception as e:
            print(f"Error updating article: {str(e)}")
            flash('حدث خطأ أثناء تحديث المقالة', 'error')
    
    try:
        if db:
            article_ref = db.collection('blogs').document(blog_id).collection('articles').document(article_id)
            article = article_ref.get()
            if article.exists:
                blog_ref = db.collection('blogs').document(blog_id)
                blog = blog_ref.get()
                return render_template('article_form.html', 
                                     blog_id=blog_id, 
                                     article={'id': article.id, **article.to_dict()},
                                     blog={'id': blog.id, **blog.to_dict()})
        
        flash('المقالة غير موجودة', 'error')
        return redirect(url_for('view_blog', blog_id=blog_id))
    except Exception as e:
        print(f"Error loading article: {str(e)}")
        flash('حدث خطأ أثناء تحميل المقالة', 'error')
        return redirect(url_for('view_blog', blog_id=blog_id))

@app.route('/blogs/<blog_id>/articles/<article_id>')
def view_article(blog_id, article_id):
    try:
        if not db:
            raise Exception("Database not available")
            
        article_ref = db.collection('blogs').document(blog_id).collection('articles').document(article_id)
        article = article_ref.get()
        
        if not article.exists:
            flash('المقالة غير موجودة', 'error')
            return redirect(url_for('view_blog', blog_id=blog_id))
        
        blog_ref = db.collection('blogs').document(blog_id)
        blog = blog_ref.get()
        
        return render_template('article_detail.html', 
                             blog={'id': blog.id, **blog.to_dict()},
                             article={'id': article.id, **article.to_dict()})
    except Exception as e:
        print(f"Error viewing article: {str(e)}")
        flash('حدث خطأ أثناء تحميل المقالة', 'error')
        return redirect(url_for('view_blog', blog_id=blog_id))

@app.route('/blogs/<blog_id>/articles/<article_id>/delete', methods=['POST'])
def delete_article(blog_id, article_id):
    try:
        if db:
            db.collection('blogs').document(blog_id).collection('articles').document(article_id).delete()
            flash('تم حذف المقالة بنجاح', 'success')
        else:
            flash('حدث خطأ أثناء حذف المقالة', 'error')
    except Exception as e:
        print(f"Error deleting article: {str(e)}")
        flash('حدث خطأ أثناء حذف المقالة', 'error')
    return redirect(url_for('view_blog', blog_id=blog_id))

if __name__ == '__main__':
    app.run(debug=True)
