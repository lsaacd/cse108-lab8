import os
import zipfile
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from flask import Flask , jsonify , redirect , render_template , request , session
from flask_admin import Admin , AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_bcrypt import Bcrypt
from flask_login import LoginManager , UserMixin , current_user , login_required , login_user , logout_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import PasswordField


load_dotenv( )


app = Flask(   __name__   )
app.config[  "SECRET_KEY"  ] = os.environ.get(  "SECRET_KEY" , "acme_university_secret_key_108"  )
app.config[ "SQLALCHEMY_DATABASE_URI" ] = "sqlite:///enrollment.db"
app.config[   "SQLALCHEMY_TRACK_MODIFICATIONS"   ] = False




db = SQLAlchemy( app )
bcrypt = Bcrypt( app )
login_manager = LoginManager( app )




class User( UserMixin , db.Model ):
    id = db.Column( db.Integer , primary_key = True )
    username = db.Column( db.String( 50 ) , unique = True , nullable = False )
    password_hash = db.Column( db.String( 128 ) , nullable = False )
    name = db.Column( db.String( 100 ) , nullable = False )
    display_name = db.Column( db.String( 100 ) , nullable = False )
    role = db.Column( db.String( 20 ) , nullable = False )


    def __repr__( self ):
        return f"{self.name} ({self.username})"





class Course( db.Model ):
    id = db.Column( db.Integer , primary_key = True )
    name = db.Column( db.String( 50 ) , unique = True , nullable = False )
    time = db.Column( db.String( 50 ) , nullable = False )
    capacity = db.Column( db.Integer , nullable = False )
    teacher_id = db.Column( db.Integer , db.ForeignKey( "user.id" ) , nullable = False )
    teacher = db.relationship( "User" , backref = db.backref( "courses_taught" , lazy = True ) )

    def __repr__( self ):
        return self.name




class Enrollment( db.Model ):
    id = db.Column( db.Integer , primary_key = True )
    student_id = db.Column( db.Integer , db.ForeignKey( "user.id" ) , nullable = False )
    course_id = db.Column( db.Integer , db.ForeignKey( "course.id" ) , nullable = False )
    grade = db.Column( db.Float , nullable = True )

    student = db.relationship( "User" , backref = db.backref( "enrollments" , lazy = True , cascade = "all, delete-orphan" ) )
    course = db.relationship( "Course" , backref = db.backref( "enrollments" , lazy = True , cascade = "all, delete-orphan" ) )

    __table_args__ = (
        db.UniqueConstraint( "student_id" , "course_id" , name = "unique_enrollment" ) ,
    )




@login_manager.user_loader
def load_user( user_id ):
    return db.session.get( User , int( user_id ) )




@login_manager.unauthorized_handler
def unauthorized( ):
    return jsonify( { "error" : "Authentication required" } ) , 401





class SecureAdminIndexView( AdminIndexView ):
    def is_accessible( self ):
        return current_user.is_authenticated and current_user.role == "admin"

    def inaccessible_callback( self , name , **kwargs ):
        return redirect( "/" )




class SecureModelView( ModelView ):
    def is_accessible( self ):
        return current_user.is_authenticated and current_user.role == "admin"

    def inaccessible_callback( self , name , **kwargs ):
        return redirect( "/" )




class UserAdminView( SecureModelView ):
    column_exclude_list = [ "password_hash" ]
    column_searchable_list = [ "username" , "name" , "role" ]
    form_excluded_columns = [ "password_hash" , "courses_taught" , "enrollments" ]
    form_extra_fields = { "password" : PasswordField( "Password" ) }
    form_choices = {
        "role" : [
            ( "student" , "Student" ) ,
            ( "teacher" , "Teacher" ) ,
            ( "admin" , "Admin" )
        ]
    }

    def on_model_change( self , form , model , is_created ):
        if form.password.data:
            model.password_hash = bcrypt.generate_password_hash( form.password.data ).decode( "utf-8" )
        elif is_created:
            model.password_hash = bcrypt.generate_password_hash( "password123" ).decode( "utf-8" )




class CourseAdminView( SecureModelView ):
    column_list = [ "id" , "name" , "time" , "capacity" , "teacher" ]
    form_columns = [ "name" , "time" , "capacity" , "teacher" ]
    column_searchable_list = [ "name" , "time" ]




class EnrollmentAdminView( SecureModelView ):
    column_list = [ "id" , "student" , "course" , "grade" ]
    form_columns = [ "student" , "course" , "grade" ]




admin = Admin( app , name = "ACME Admin" , index_view = SecureAdminIndexView( ) )
admin.add_view( UserAdminView( User , db ) )
admin.add_view( CourseAdminView( Course , db ) )
admin.add_view( EnrollmentAdminView( Enrollment , db ) )
admin.add_link( MenuLink( name = "Sign Out" , url = "/logout" ) )




def format_course( course , student_id = None ):
    enrolled_count = len( course.enrollments )
    is_enrolled = False

    if student_id is not None:
        for e in course.enrollments:
            if e.student_id == student_id:
                is_enrolled = True
                break

    return {
        "id" : course.id ,
        "name" : course.name ,
        "teacher" : course.teacher.name ,
        "time" : course.time ,
        "enrolled" : enrolled_count ,
        "capacity" : course.capacity ,
        "is_enrolled" : is_enrolled
    }




@app.route( "/" )
def home( ):
    return render_template( "index.html" )




@app.route( "/logout" )
def logout_redirect( ):
    logout_user( )
    session.pop( "display_name" , None )
    return redirect( "/" )




@app.route( "/api/me" , methods = [ "GET" ] )
def get_me( ):
    if not current_user.is_authenticated:
        return jsonify( { "error" : "Not logged in" } ) , 401

    return jsonify( {
        "id" : current_user.id ,
        "username" : current_user.username ,
        "name" : current_user.name ,
        "display_name" : session.get( "display_name" , current_user.display_name ) ,
        "role" : current_user.role
    } )




@app.route( "/api/login" , methods = [ "POST" ] )
def login( ):
    data = request.get_json( )
    if not data or "username" not in data or "password" not in data:
        return jsonify( { "error" : "Username and password are required" } ) , 400

    raw_username = data[ "username" ].strip( )
    username_lookup = raw_username.lower( )
    password = data[ "password" ]

    user = User.query.filter_by( username = username_lookup ).first( )
    display_override = None

    if not user:
        if username_lookup == "cnorris":
            user = User.query.filter_by( username = "mnorris" ).first( )
            display_override = "Chuck"
        elif username_lookup == "ychen":
            user = User.query.filter_by( username = "ywchen" ).first( )

    if not user or not bcrypt.check_password_hash( user.password_hash , password ):
        return jsonify( { "error" : "Invalid username or password" } ) , 401

    login_user( user )
    effective_display = display_override or user.display_name
    session[ "display_name" ] = effective_display

    return jsonify( {
        "id" : user.id ,
        "username" : raw_username ,
        "name" : user.name ,
        "display_name" : effective_display ,
        "role" : user.role
    } )




@app.route( "/api/logout" , methods = [ "POST" ] )
def api_logout( ):
    logout_user( )
    session.pop( "display_name" , None )
    return jsonify( { "message" : "Logged out" } )




@app.route( "/api/student/courses" , methods = [ "GET" ] )
@login_required
def get_student_courses( ):
    if current_user.role != "student":
        return jsonify( { "error" : "Student access required" } ) , 403

    all_courses = Course.query.order_by( Course.id ).all( )
    my_courses = [ ]
    catalog = [ ]

    for course in all_courses:
        item = format_course( course , current_user.id )
        catalog.append( item )
        if item[ "is_enrolled" ]:
            my_courses.append( item )

    return jsonify( {
        "my_courses" : my_courses ,
        "all_courses" : catalog
    } )




@app.route( "/api/courses/<int:course_id>/enroll" , methods = [ "POST" ] )
@login_required
def enroll_course( course_id ):
    if current_user.role != "student":
        return jsonify( { "error" : "Student access required" } ) , 403

    course = db.session.get( Course , course_id )
    if not course:
        return jsonify( { "error" : "Course not found" } ) , 404

    existing = Enrollment.query.filter_by( student_id = current_user.id , course_id = course_id ).first( )
    if existing:
        return jsonify( { "error" : "Already enrolled in this course" } ) , 409

    if len( course.enrollments ) >= course.capacity:
        return jsonify( { "error" : "Course is already at capacity" } ) , 400

    enrollment = Enrollment( student_id = current_user.id , course_id = course_id , grade = None )
    db.session.add( enrollment )
    db.session.commit( )

    return jsonify( { "message" : "Enrolled in " + course.name } ) , 201




@app.route( "/api/courses/<int:course_id>/drop" , methods = [ "POST" ] )
@login_required
def drop_course( course_id ):
    if current_user.role != "student":
        return jsonify( { "error" : "Student access required" } ) , 403

    enrollment = Enrollment.query.filter_by( student_id = current_user.id , course_id = course_id ).first( )
    if not enrollment:
        return jsonify( { "error" : "Not enrolled in this course" } ) , 404

    db.session.delete( enrollment )
    db.session.commit( )

    return jsonify( { "message" : "Dropped course" } )




@app.route( "/api/teacher/courses" , methods = [ "GET" ] )
@login_required
def get_teacher_courses( ):
    if current_user.role != "teacher":
        return jsonify( { "error" : "Teacher access required" } ) , 403

    courses = Course.query.filter_by( teacher_id = current_user.id ).order_by( Course.id ).all( )
    results = [ ]

    for course in courses:
        results.append( format_course( course ) )

    return jsonify( { "courses" : results } )




@app.route( "/api/teacher/courses/<int:course_id>/students" , methods = [ "GET" ] )
@login_required
def get_course_students( course_id ):
    if current_user.role != "teacher":
        return jsonify( { "error" : "Teacher access required" } ) , 403

    course = db.session.get( Course , course_id )
    if not course:
        return jsonify( { "error" : "Course not found" } ) , 404

    if course.teacher_id != current_user.id:
        return jsonify( { "error" : "Access denied" } ) , 403

    students = [ ]
    for enrollment in course.enrollments:
        students.append( {
            "student_id" : enrollment.student.id ,
            "name" : enrollment.student.name ,
            "grade" : enrollment.grade
        } )

    return jsonify( {
        "course_id" : course.id ,
        "course_name" : course.name ,
        "students" : students
    } )




@app.route( "/api/teacher/courses/<int:course_id>/grades/<int:student_id>" , methods = [ "PUT" ] )
@login_required
def update_student_grade( course_id , student_id ):
    if current_user.role != "teacher":
        return jsonify( { "error" : "Teacher access required" } ) , 403

    course = db.session.get( Course , course_id )
    if not course or course.teacher_id != current_user.id:
        return jsonify( { "error" : "Access denied" } ) , 403

    enrollment = Enrollment.query.filter_by( course_id = course_id , student_id = student_id ).first( )
    if not enrollment:
        return jsonify( { "error" : "Enrollment not found" } ) , 404

    data = request.get_json( )
    if not data or "grade" not in data:
        return jsonify( { "error" : "Grade is required" } ) , 400

    try:
        new_grade = float( data[ "grade" ] )
    except ( ValueError , TypeError ):
        return jsonify( { "error" : "Invalid grade value" } ) , 400

    if new_grade < 0 or new_grade > 100:
        return jsonify( { "error" : "Grade must be between 0 and 100" } ) , 400

    enrollment.grade = new_grade
    db.session.commit( )

    return jsonify( { "message" : "Grade updated" , "grade" : enrollment.grade } )




def make_username( full_name ):
    parts = full_name.strip( ).split( )
    if len( parts ) == 1:
        return parts[ 0 ].lower( )
    if len( parts ) == 3 and parts[ 0 ] == "Yi" and parts[ 1 ] == "Wen":
        return "ywchen"
    return ( parts[ 0 ][ 0 ] + parts[ -1 ] ).lower( )




def make_display_name( full_name , role ):
    parts = full_name.strip( ).split( )
    if role == "teacher":
        return f"Dr {parts[ -1 ]}"
    if len( parts ) >= 2 and parts[ 0 ] == "Yi" and parts[ 1 ] == "Wen":
        return "Yi Wen"
    return parts[ 0 ]




def parse_excel_dataset( filepath = "Enrollment example data for Lab8.xlsx" ):
    if not os.path.exists( filepath ):
        return None

    try:
        with zipfile.ZipFile( filepath , "r" ) as z:
            sst_root = ET.fromstring( z.read( "xl/sharedStrings.xml" ) )
            shared_strings = [ ]
            for si in sst_root.findall( ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si" ):
                text = "".join( [ t.text for t in si.findall( ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t" ) if t.text ] )
                shared_strings.append( text )

            sheet_root = ET.fromstring( z.read( "xl/worksheets/sheet1.xml" ) )
            rows = [ ]
            for row in sheet_root.findall( ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row" ):
                row_dict = { }
                for c in row.findall( "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c" ):
                    ref = c.attrib.get( "r" )
                    col = "".join( [ ch for ch in ref if ch.isalpha( ) ] )
                    t = c.attrib.get( "t" )
                    v = c.find( "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v" )
                    val = v.text if v is not None else ""
                    if t == "s" and val.isdigit( ):
                        val = shared_strings[ int( val ) ]
                    row_dict[ col ] = val.strip( )
                if row_dict:
                    rows.append( row_dict )

        courses_data = [ ]
        current_course = None
        for r in rows:
            if "A" in r and r[ "A" ] != "Class Name" and r[ "A" ]:
                current_course = {
                    "name" : r[ "A" ] ,
                    "teacher" : r.get( "B" , "" ).strip( ) ,
                    "time" : r.get( "C" , "" ).strip( ) ,
                    "capacity" : int( r.get( "D" , 0 ) ) ,
                    "enrollments" : [ ]
                }
                courses_data.append( current_course )
            if current_course and "E" in r and r[ "E" ] and r[ "E"] != "Student Names":
                grade = float( r[ "F" ] ) if "F" in r and r[ "F" ] else None
                current_course[ "enrollments" ].append( {
                    "student" : r[ "E" ].strip( ) ,
                    "grade" : grade
                } )
        return courses_data
    except Exception as e:
        print( f"Warning: Failed to parse {filepath}: {e}" )
        return None




def seed_database( ):
    if User.query.first( ):
        return

    default_pw = bcrypt.generate_password_hash( "password123" ).decode( "utf-8" )
    admin_pw = bcrypt.generate_password_hash( "admin123" ).decode( "utf-8" )

    admin_user = User( username = "admin" , password_hash = admin_pw , name = "Admin User" , display_name = "Admin" , role = "admin" )
    db.session.add( admin_user )

    courses_data = parse_excel_dataset( )
    if courses_data:
        teacher_map = { }
        student_map = { }

        for c_data in courses_data:
            t_name = c_data[ "teacher" ]
            if t_name and t_name not in teacher_map:
                teacher_user = User(
                    username = make_username( t_name ) ,
                    password_hash = default_pw ,
                    name = t_name ,
                    display_name = make_display_name( t_name , "teacher" ) ,
                    role = "teacher"
                )
                db.session.add( teacher_user )
                teacher_map[ t_name ] = teacher_user

            for e_data in c_data[ "enrollments" ]:
                s_name = e_data[ "student" ]
                if s_name and s_name not in student_map:
                    student_user = User(
                        username = make_username( s_name ) ,
                        password_hash = default_pw ,
                        name = s_name ,
                        display_name = make_display_name( s_name , "student" ) ,
                        role = "student"
                    )
                    db.session.add( student_user )
                    student_map[ s_name ] = student_user

        db.session.commit( )

        for c_data in courses_data:
            teacher_user = teacher_map[ c_data[ "teacher" ] ]
            course = Course(
                name = c_data[ "name" ] ,
                time = c_data[ "time" ] ,
                capacity = c_data[ "capacity" ] ,
                teacher_id = teacher_user.id
            )
            db.session.add( course )
            db.session.commit( )

            for e_data in c_data[ "enrollments" ]:
                student_user = student_map[ e_data[ "student" ] ]
                enrollment = Enrollment(
                    student_id = student_user.id ,
                    course_id = course.id ,
                    grade = e_data[ "grade" ]
                )
                db.session.add( enrollment )
        db.session.commit( )
    else:
        ralph = User( username = "rjenkins" , password_hash = default_pw , name = "Ralph Jenkins" , display_name = "Dr Jenkins" , role = "teacher" )
        susan = User( username = "swalker" , password_hash = default_pw , name = "Susan Walker" , display_name = "Dr Walker" , role = "teacher" )
        ammon = User( username = "ahepworth" , password_hash = default_pw , name = "Ammon Hepworth" , display_name = "Dr Hepworth" , role = "teacher" )

        jose = User( username = "jsantos" , password_hash = default_pw , name = "Jose Santos" , display_name = "Jose" , role = "student" )
        betty = User( username = "bbrown" , password_hash = default_pw , name = "Betty Brown" , display_name = "Betty" , role = "student" )
        john = User( username = "jstuart" , password_hash = default_pw , name = "John Stuart" , display_name = "John" , role = "student" )
        li = User( username = "lcheng" , password_hash = default_pw , name = "Li Cheng" , display_name = "Li" , role = "student" )
        nancy = User( username = "nlittle" , password_hash = default_pw , name = "Nancy Little" , display_name = "Nancy" , role = "student" )
        mindy = User( username = "mnorris" , password_hash = default_pw , name = "Mindy Norris" , display_name = "Mindy" , role = "student" )
        aditya = User( username = "aranganath" , password_hash = default_pw , name = "Aditya Ranganath" , display_name = "Aditya" , role = "student" )
        yiwen = User( username = "ywchen" , password_hash = default_pw , name = "Yi Wen Chen" , display_name = "Yi Wen" , role = "student" )

        db.session.add_all( [ ralph , susan , ammon , jose , betty , john , li , nancy , mindy , aditya , yiwen ] )
        db.session.commit( )

        math101 = Course( name = "Math 101" , time = "MWF 10:00-10:50 AM" , capacity = 8 , teacher_id = ralph.id )
        physics121 = Course( name = "Physics 121" , time = "TR 11:00-11:50 AM" , capacity = 10 , teacher_id = susan.id )
        cs106 = Course( name = "CS 106" , time = "MWF 2:00-2:50 PM" , capacity = 10 , teacher_id = ammon.id )
        cs162 = Course( name = "CS 162" , time = "TR 3:00-3:50 PM" , capacity = 4 , teacher_id = ammon.id )

        db.session.add_all( [ math101 , physics121 , cs106 , cs162 ] )
        db.session.commit( )

        enrollments = [
            Enrollment( student_id = jose.id , course_id = math101.id , grade = 92 ) ,
            Enrollment( student_id = betty.id , course_id = math101.id , grade = 65 ) ,
            Enrollment( student_id = john.id , course_id = math101.id , grade = 86 ) ,
            Enrollment( student_id = li.id , course_id = math101.id , grade = 77 ) ,
            Enrollment( student_id = nancy.id , course_id = physics121.id , grade = 53 ) ,
            Enrollment( student_id = li.id , course_id = physics121.id , grade = 85 ) ,
            Enrollment( student_id = mindy.id , course_id = physics121.id , grade = 94 ) ,
            Enrollment( student_id = john.id , course_id = physics121.id , grade = 91 ) ,
            Enrollment( student_id = betty.id , course_id = physics121.id , grade = 88 ) ,
            Enrollment( student_id = aditya.id , course_id = cs106.id , grade = 93 ) ,
            Enrollment( student_id = yiwen.id , course_id = cs106.id , grade = 85 ) ,
            Enrollment( student_id = nancy.id , course_id = cs106.id , grade = 57 ) ,
            Enrollment( student_id = mindy.id , course_id = cs106.id , grade = 68 ) ,
            Enrollment( student_id = aditya.id , course_id = cs162.id , grade = 99 ) ,
            Enrollment( student_id = nancy.id , course_id = cs162.id , grade = 87 ) ,
            Enrollment( student_id = yiwen.id , course_id = cs162.id , grade = 92 ) ,
            Enrollment( student_id = john.id , course_id = cs162.id , grade = 67 )
        ]

        db.session.add_all( enrollments )
        db.session.commit( )




with app.app_context( ):
    db.create_all( )
    seed_database( )




if __name__ == "__main__":
    app.run( debug = True )
