const   loginHeader= document.getElementById( "login-header" );
  const appHeader  =document.getElementById("app-header" );
const welcomeText =   document.getElementById( "welcome-text" ) ;
    const signOutLink=document.getElementById(  "sign-out-link");
const statusBox   = document.getElementById("status-box" );

 const loginSection =  document.getElementById( "login-section"  );
const  loginForm=document.getElementById("login-form" );
   const usernameInput=document.getElementById( "username" );
const passwordInput  =   document.getElementById( "password" );

  const studentSection = document.getElementById(  "student-section" );
const tabMyCourses=document.getElementById( "tab-my-courses"  );
      const tabAddCourses = document.getElementById( "tab-add-courses" );
const myCoursesView=  document.getElementById( "my-courses-view" );
 const addCoursesView   = document.getElementById( "add-courses-view" );
const studentMyCoursesBody =document.getElementById("student-my-courses-body" );
   const studentAllCoursesBody=  document.getElementById( "student-all-courses-body" );

const teacherSection=document.getElementById( "teacher-section" );
  const teacherCoursesView=   document.getElementById("teacher-courses-view" );
    const teacherRosterView =document.getElementById( "teacher-roster-view" );
const teacherCoursesBody=  document.getElementById("teacher-courses-body" );
 const teacherRosterBody = document.getElementById( "teacher-roster-body" );
const rosterCourseTitle=   document.getElementById("roster-course-title" );
   const backToCoursesBtn= document.getElementById( "back-to-courses-btn" );



let   statusTimer =null ;
let activeCourseId= null;



function showStatus( message ,type ){
   if( statusTimer ){
        clearTimeout( statusTimer ) ;
   }

statusBox.textContent = message ;
    statusBox.className= "status-box status-" +   type;
 statusBox.style.display="block" ;



 statusTimer= setTimeout( function( ){
       statusBox.style.display= "none" ;
  } , 3500 );
}



function  showLoginView( ){
 loginHeader.classList.remove( "hidden" );
    appHeader.classList.add( "hidden" );
 loginSection.classList.remove( "hidden" );
   studentSection.classList.add( "hidden" );
       teacherSection.classList.add( "hidden" );
  usernameInput.value= "" ;
passwordInput.value = "";
}



function showPortalForUser( user ){
 if( user.role ==="admin" ){
     window.location.href= "/admin" ;
    return ;
 }

 loginHeader.classList.add( "hidden" );
  appHeader.classList.remove( "hidden" );
     loginSection.classList.add( "hidden" );
welcomeText.textContent="Welcome " +  user.display_name +"!" ;


   if( user.role === "student" ){
      teacherSection.classList.add( "hidden" );
   studentSection.classList.remove( "hidden" );
       switchStudentTab( "my" );
    loadStudentCourses( );
   }else if( user.role=== "teacher" ){
 studentSection.classList.add( "hidden" );
     teacherSection.classList.remove( "hidden" );
         showTeacherCoursesList( );
      loadTeacherCourses( );
   }
}



function switchStudentTab( tab ){
   if( tab ==="my" ){
    tabMyCourses.classList.add( "active" );
      tabAddCourses.classList.remove( "active" );
   myCoursesView.classList.remove( "hidden" );
        addCoursesView.classList.add( "hidden" );
 } else {
      tabAddCourses.classList.add( "active" );
  tabMyCourses.classList.remove( "active" );
     addCoursesView.classList.remove( "hidden" );
        myCoursesView.classList.add( "hidden" );
   }
}



function  checkSession( ){
  const xhttp = new XMLHttpRequest( );
    xhttp.open( "GET" , "/api/me" , true );
  xhttp.send( );

 xhttp.onload = function( ){
       if( this.status === 200 ){
   const user = JSON.parse( this.responseText );
         showPortalForUser( user );
     } else {
        showLoginView( );
       }
 };
}



function handleLogin( event ){
 event.preventDefault( );
   const username= usernameInput.value.trim( );
    const password =passwordInput.value ;

 const xhttp= new XMLHttpRequest( );
     xhttp.open( "POST" , "/api/login" , true );
  xhttp.setRequestHeader( "Content-Type" ,"application/json" );
     xhttp.send( JSON.stringify( { username : username , password : password } ) );


    xhttp.onload =function( ){
       if( this.status===200 ){
  const user =JSON.parse( this.responseText );
        statusBox.style.display= "none";
     showPortalForUser( user );
        }else {
     const err= JSON.parse( this.responseText );
        showStatus( err.error || "Login failed" , "error" );
   }
    };
}



function handleLogout( event ){
   event.preventDefault( );
 const xhttp =new XMLHttpRequest( );
     xhttp.open( "POST" , "/api/logout" , true );
  xhttp.send( );

    xhttp.onload= function( ){
 statusBox.style.display = "none" ;
      showLoginView( );
  };
}



function createTextCell( text ){
   const td= document.createElement( "td" );
 td.textContent = text ;
    return td ;
}



function loadStudentCourses( ){
  const xhttp= new XMLHttpRequest( );
     xhttp.open( "GET" , "/api/student/courses" , true );
  xhttp.send( );

  xhttp.onload= function( ){
     if( this.status !== 200 ){
        showStatus( "Failed to load courses" ,"error" );
       return ;
     }

   const data= JSON.parse( this.responseText );
       renderStudentMyCourses( data.my_courses );
     renderStudentAllCourses( data.all_courses );
 };
}



function renderStudentMyCourses( courses ){
 studentMyCoursesBody.innerHTML ="" ;
  if( courses.length=== 0 ){
    studentMyCoursesBody.innerHTML= '<tr><td colspan="4" class="empty-cell">You are not enrolled in any courses</td></tr>';
      return;
  }

 for( let i= 0 ; i < courses.length ; i++ ){
     const c = courses[ i ];
   const tr= document.createElement( "tr" );
     tr.appendChild( createTextCell( c.name ) );
   tr.appendChild( createTextCell( c.teacher ) );
       tr.appendChild( createTextCell( c.time ) );
   tr.appendChild( createTextCell( c.enrolled+ "/" + c.capacity ) );
       studentMyCoursesBody.appendChild( tr );
   }
}



function renderStudentAllCourses( courses ){
    studentAllCoursesBody.innerHTML = "" ;

 for( let i =0 ; i< courses.length; i++ ){
     const c =courses[ i ];
   const tr = document.createElement( "tr" );
       tr.appendChild( createTextCell( c.name ) );
   tr.appendChild( createTextCell( c.teacher ) );
     tr.appendChild( createTextCell( c.time ) );
   tr.appendChild( createTextCell( c.enrolled + "/" + c.capacity ) );


   const actionTd = document.createElement( "td" );
       actionTd.className= "action-cell" ;

      if( c.is_enrolled ){
       const dropBtn= document.createElement( "button" );
         dropBtn.type= "button" ;
       dropBtn.className= "drop-btn" ;
         dropBtn.textContent= "-" ;
       dropBtn.addEventListener( "click" , function( ){
            dropCourse( c.id );
         } );
      actionTd.appendChild( dropBtn );
   } else if( c.enrolled< c.capacity ){
       const addBtn= document.createElement( "button" );
         addBtn.type = "button" ;
       addBtn.className = "enroll-btn" ;
         addBtn.textContent= "+" ;
       addBtn.addEventListener( "click" , function( ){
            enrollCourse( c.id );
        } );
      actionTd.appendChild( addBtn );
   }

    tr.appendChild( actionTd );
        studentAllCoursesBody.appendChild( tr );
 }
}



function enrollCourse( courseId ){
  const xhttp= new XMLHttpRequest( );
    xhttp.open( "POST" , "/api/courses/" + courseId + "/enroll" , true );
  xhttp.send( );

  xhttp.onload= function( ){
   const data = JSON.parse( this.responseText );
       if( this.status ===201 ){
     showStatus( data.message , "success" );
          loadStudentCourses( );
     } else {
        showStatus( data.error || "Could not enroll" , "error" );
     }
  };
}



function dropCourse( courseId ){
   const xhttp = new XMLHttpRequest( );
  xhttp.open( "POST" , "/api/courses/" + courseId + "/drop" , true );
     xhttp.send( );

 xhttp.onload = function( ){
    const data= JSON.parse( this.responseText );
        if( this.status=== 200 ){
      showStatus( data.message ,"success" );
           loadStudentCourses( );
      } else {
         showStatus( data.error|| "Could not drop course" , "error" );
      }
 };
}



function showTeacherCoursesList( ){
   teacherRosterView.classList.add( "hidden" );
 teacherCoursesView.classList.remove( "hidden" );
}



function loadTeacherCourses( ){
  const xhttp =new XMLHttpRequest( );
    xhttp.open( "GET" , "/api/teacher/courses" , true );
 xhttp.send( );

 xhttp.onload = function( ){
     if( this.status !== 200 ){
        showStatus( "Failed to load courses" , "error" );
         return ;
     }

   const data= JSON.parse( this.responseText );
       renderTeacherCourses( data.courses );
 };
}



function renderTeacherCourses( courses ){
  teacherCoursesBody.innerHTML= "" ;
   if( courses.length === 0 ){
    teacherCoursesBody.innerHTML = '<tr><td colspan="4" class="empty-cell">No courses assigned</td></tr>' ;
       return ;
   }


  for( let i= 0 ; i< courses.length ; i++ ){
     const c = courses[ i ];
   const tr= document.createElement( "tr" );

     const nameTd = document.createElement( "td" );
   const link= document.createElement( "a" );
       link.href ="#" ;
     link.className = "course-link" ;
       link.textContent = c.name ;
     link.addEventListener( "click" , function( e ){
          e.preventDefault( );
        openCourseRoster( c.id );
     } );
      nameTd.appendChild( link );
    tr.appendChild( nameTd );

    tr.appendChild( createTextCell( c.teacher ) );
        tr.appendChild( createTextCell( c.time ) );
    tr.appendChild( createTextCell( c.enrolled+ "/" + c.capacity ) );
       teacherCoursesBody.appendChild( tr );
  }
}



function openCourseRoster( courseId ){
    activeCourseId =courseId ;
 const xhttp= new XMLHttpRequest( );
     xhttp.open( "GET" , "/api/teacher/courses/" + courseId + "/students" , true );
  xhttp.send( );

    xhttp.onload= function( ){
      if( this.status!== 200 ){
        showStatus( "Failed to load students" , "error" );
          return;
      }

    const data = JSON.parse( this.responseText );
        rosterCourseTitle.textContent = data.course_name ;
      renderRoster( data.students );
        teacherCoursesView.classList.add( "hidden" );
      teacherRosterView.classList.remove( "hidden" );
    };
}



function renderRoster( students ){
 teacherRosterBody.innerHTML ="" ;
   if( students.length=== 0 ){
    teacherRosterBody.innerHTML ='<tr><td colspan="2" class="empty-cell">No students enrolled</td></tr>' ;
       return;
   }

 for( let i= 0 ; i < students.length ; i++ ){
     const s= students[ i ];
   const tr = document.createElement( "tr" );
       tr.appendChild( createTextCell( s.name ) );

   const gradeTd =document.createElement( "td" );
       const wrap= document.createElement( "div" );
   wrap.className = "grade-edit-wrap" ;


   const gradeInput = document.createElement( "input" );
       gradeInput.type= "number" ;
   gradeInput.step = "0.1" ;
       gradeInput.min= "0" ;
   gradeInput.max= "100" ;
       gradeInput.className ="grade-input" ;
   gradeInput.value = ( s.grade !== null ) ? s.grade : "" ;

     const saveBtn = document.createElement( "button" );
   saveBtn.type= "button" ;
       saveBtn.className = "save-grade-btn" ;
   saveBtn.textContent ="Save" ;
       saveBtn.addEventListener( "click" , function( ){
         saveGrade( activeCourseId , s.student_id , gradeInput.value );
      } );

   gradeInput.addEventListener( "keypress" , function( e ){
        if( e.key=== "Enter" ){
           saveGrade( activeCourseId , s.student_id , gradeInput.value );
        }
   } );

     gradeInput.addEventListener( "change" , function( ){
        saveGrade( activeCourseId , s.student_id , gradeInput.value );
     } );

    wrap.appendChild( gradeInput );
        wrap.appendChild( saveBtn );
    gradeTd.appendChild( wrap );
        tr.appendChild( gradeTd );
   teacherRosterBody.appendChild( tr );
 }
}



function saveGrade( courseId , studentId , gradeValue ){
   if( gradeValue=== "" ){
    showStatus( "Please enter a grade" , "error" );
       return ;
   }

 const xhttp= new XMLHttpRequest( );
    xhttp.open( "PUT" , "/api/teacher/courses/" + courseId + "/grades/" + studentId , true );
  xhttp.setRequestHeader( "Content-Type" , "application/json" );
      xhttp.send( JSON.stringify( { grade : parseFloat( gradeValue ) } ) );


   xhttp.onload = function( ){
     const data = JSON.parse( this.responseText );
         if( this.status === 200 ){
        showStatus( "Grade updated to " + data.grade , "success" );
         } else {
        showStatus( data.error || "Failed to update grade" , "error" );
         }
   };
}



loginForm.addEventListener( "submit" , handleLogin );
  signOutLink.addEventListener( "click" , handleLogout );
tabMyCourses.addEventListener( "click" , function( ){
    switchStudentTab( "my" );
 } );
   tabAddCourses.addEventListener( "click" , function( ){
   switchStudentTab( "add" );
} );
backToCoursesBtn.addEventListener( "click" , function( ){
    showTeacherCoursesList( );
  loadTeacherCourses( );
} );

document.addEventListener( "DOMContentLoaded" , checkSession );
