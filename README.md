# iQuiz

## Introduction

iQuiz is an LTI compliant Python (Django) application for creating and offering quizzes in MOOCs platforms. It can easily be integrated with LTI consumers (tested only with Open edX currently), and the instructor can start creating the quizzes they want to offer. iQuiz can be extended and modified to support various types of questions as required.

---

# Getting Started

To use iQuiz, first install the iQuiz on the server (local machine for development), and then to use it in the openEdx, we have to 
The installation process of iQuiz is same as that of installing a django application on a server. For deployment in production, you **must** enable the SSL certificate to encrypt the data being transferred as LTI (OAuth) relies on the HTTPS for security. 
You can follow any guide available on internet to deploy Django Applications while in production , but if you don't want to invest time in deployment, then you can consider checking out [Python Anywhere](https://www.pythonanywhere.com) or Heroku like PaaS.

The quick installation for development and testing purpose is given below:

*Instructions are for Ubuntu or Debian with Python 3.6 installed, for other system the process will slightly vary.*

## Dependencies
Major libraries include :

* [django](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [pyLTI](https://github.com/mitodl/pylti) - Used as LTI library
* [lti](https://github.com/pylti/lti) - Used as LTI library (for django request authentication)


## Installing
0. Install `pip` and `virtualenv`
```
$ sudo apt-get update                   # update apt-get
$ sudo apt-get install python3-pip      # install pip if not already
$ sudo apt-get install virtualenv       # install virtualenv to use virtual environment (good idea!)
```

1. Create a virtual enviroment using virtualenv in a directory and activate it.
```
$ mkdir iQuiz && cd iQuiz
$ virtualenv . --python=python3.6     # creates a virtual enviroment in the directory iQuiz
$ source bin/activate
```

2. Clone the repository with git to local system.
```
$ git clone https://www.github.com/anitagoel/iQuiz
```

3. Install the requirements for iQuiz in the python virtual envrionement.
```
$ cd iQuiz
$ pip install -r requirements.txt       # this will install the listing as in requirements.txt
```

4. Run the development server
```
$ python manage.py runserver 0.0.0.0:8000
```

## Integrating with LMS (Open edX)

To integrate with Open edX, follow the steps given below:

### TODO : Explanation here


## Pictures

### Student's Homepage
---
![Student Homepage View](/demo_images/student_views/student_home.png)

### Student's Quiz Attempt
---
![Student's Quiz Attempt Live View](/demo_images/student_views/student_attempt_live.png)

### Instructor's Homepage
---
![Instructor Homepage View](/demo_images/teacher_views/teachers_home.png)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
