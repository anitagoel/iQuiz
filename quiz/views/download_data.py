from quiz.models.response import Response
import xlwt, json
from django.http import HttpResponse
from quiz.utils.decorators import *
from datetime import datetime


def download_grade_data(request):
    quiz = db.get_quiz(request)
    student_responses = db.get_students_responses(request)
    questions = list(db.get_questions_by_quiz(quiz).values())
    response = HttpResponse(content_type='application/ms-excel')

    # decide file name
    response['Content-Disposition'] = f'attachment; filename="{quiz.quizName}.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("sheet1")

    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Username/ID', 'Title', 'Location', 'Question', 'Question Difficulty', 'Chosen Option', 'Chosen Answer', 'Expected Answer', 'Correct/Incorrect', 'Answer Submission Time', 'Answer Attempts', 'Start Time', 'Time Spent (secs)', 'Score Possible', 'Score Earned', 'State', 'IP Address']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for response_obj in student_responses:
        response_json = json.loads(response_obj.response)
        questions_started = response_obj.questions_start_time
        for question in response_obj.question_ids:
            response_json.setdefault(str(question), [])
        for question_id in response_json:
            row_num = row_num + 1
            question = quiz.question_set.filter(pk=question_id).first()
            expected_response = question.expected_response
            student_response = response_json[question_id]
            most_recent_response = ('Unanswered', 0)
            if len(student_response) > 0:
                chosen_answer = student_response[-1][0]
                most_recent_response = student_response[-1]
                answer_submission_time = datetime.fromtimestamp(most_recent_response[1]).strftime('%d-%m-%Y %H:%M:%S')
            else:
                chosen_answer = None
                answer_submission_time = 'Unasnswered'
            if (question.question_type == 'MCQ' or question.question_type == 'VMCQ') and chosen_answer is not None:
                options = json.loads(question.options_data)
                chosen_answer = [option for option in options if option[0] == chosen_answer][0][1]
                expected_answer = [option for option in options if option[0] == expected_response][0][1]

                correct_incorrect = 'Correct' if chosen_answer == expected_answer else 'Incorrect'
            else:
                expected_answer = expected_response
                correct_incorrect = 'Correct' if chosen_answer == expected_answer else 'Incorrect'
                if question.question_type == 'SAQ':
                    correct_incorrect = 'Answered' if student_response[-1][0] != '' else 'Unanswered'
            answer_object = question.answer_set.filter(response=response_obj).first()
            question_start_time = questions_started.get(question_id, 'Not Recorded')
            if question_start_time != 'Not Recorded':
                print(question_start_time)
                question_start_time = datetime.fromtimestamp(int(question_start_time)).strftime('%d-%m-%Y %H:%M:%S')
            time_spent = 0
            if answer_object:
                time_spent = answer_object.time_spent

            for data in student_response:
                data[1] = datetime.fromtimestamp(data[1]).strftime('%d-%m-%Y %H:%M:%S')

            ws.write(row_num, 0, response_obj.user.name, font_style)
            ws.write(row_num, 1, question.question_type, font_style)
            ws.write(row_num, 2, f'{quiz.contextTitle} > {quiz.quizName} > {question.question_type}', font_style)
            ws.write(row_num, 3, question.statement, font_style)
            ws.write(row_num, 4, question.question_difficulty, font_style)
            ws.write(row_num, 5, most_recent_response[0], font_style)
            # ws.write(row_num, 3, [option[1] for option in options if option[0] == expected_response][0], font_style)
            ws.write(row_num, 6, chosen_answer, font_style)
            ws.write(row_num, 7, expected_answer, font_style)
            ws.write(row_num, 8, correct_incorrect, font_style)
            ws.write(row_num, 9, answer_submission_time, font_style)
            ws.write(row_num, 10, len(student_response))
            ws.write(row_num, 11, question_start_time, font_style)
            ws.write(row_num, 12, time_spent)
            ws.write(row_num, 13, question.question_weight)
            ws.write(row_num, 14, question.question_weight if chosen_answer == expected_answer else 0)
            ws.write(row_num, 15, json.dumps(student_response))
            ws.write(row_num, 16, response_obj.ip_address)
    wb.save(response)
    return response


def download_report_data(request, attempt_id):
    
    quiz = db.get_quiz(request)
    student_responses = Response.objects.filter(pk=attempt_id)
    student = student_responses.first().user

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{student.id}_{student.name}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("sheet1")

    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Username/ID', 'Exam ID', 'Question ID', 'Question Difficulty', 'Question Type', 'Question Location', 'Possible Score', 'Earned Score', 'Correct Response', 'Draft Response with timestamps', 'Final Response', 'Time Spent (secs)', 'Submission Time']
    exam_id = f'{quiz.createdOn.strftime("%d-%m-%Y")}_{quiz.resourceLinkId}_{quiz.contextId}'

    # if quiz.maxAttempts is not None:
    #     columns.append('Attempts')
    #     ws.write(row_num, 9, )
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for response_obj in student_responses:
        response_json = json.loads(response_obj.response)
        # Set default value if question is not answered
        for question in response_obj.question_ids:
            response_json.setdefault(str(question), [])
        for question_id in response_json:
            row_num = row_num + 1
            question = quiz.question_set.filter(pk=question_id).first()
            answer_object = question.answer_set.filter(response=response_obj).first()
            # get time spent on that question
            time_spent = 0
            if answer_object:
                time_spent = answer_object.time_spent
            expected_response = question.expected_response # It is the option expected from student
            student_response = response_json[question_id] # List of tuples
            for data in student_response:
                data[1] = datetime.fromtimestamp(data[1]).strftime('%d-%m-%Y %H:%M:%S')
            most_recent_response_and_timestamp = ('Unanswered', 0) # Response if unanswered
            if len(student_response) > 0:
                most_recent_response_and_timestamp = student_response[-1]
                chosen_response = most_recent_response_and_timestamp[0] # Chosen option
                answer_submission_time = most_recent_response_and_timestamp[1]
            else:
                chosen_response = None
                chosen_answer = None # Since not answered, answer is None
                answer_submission_time = 'Unanswered'
            # Finding option value of response and expected_answer
            if (question.question_type == 'MCQ' or question.question_type == 'VMCQ') and chosen_response is not None: # MCQ and answered
                options = json.loads(question.options_data)
                chosen_answer = [option for option in options if option[0] == chosen_response][0][1]
                expected_answer = [option for option in options if option[0] == expected_response][0][1]
            else:
                expected_answer = expected_response # In case of T/F or SAQ
            answered_correctly = True if chosen_response == expected_response else False
            earned_score = question.question_weight if answered_correctly else 0
            # Answered/Unanswered in SAQ
            if question.question_type == 'SAQ':
                correct_incorrect = 'Answered' if student_response[-1][0] != '' else 'Unanswered'
            values = [student.name, exam_id, question.serial_number, question.question_difficulty, question.question_type, f'{quiz.contextTitle} > {quiz.quizName}', question.question_weight, earned_score, expected_response, json.dumps(student_response), str(chosen_response), time_spent, answer_submission_time ]
            print(values)
            for index, value in enumerate(values):
                ws.write(row_num, index, value)
    wb.save(response)
    return response