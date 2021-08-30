import xlwt, json
from django.http import HttpResponse
from quiz.utils.decorators import *
from datetime import datetime


def download_excel_data(request):
    # content-type of response
    quiz = db.get_quiz(request)
    student_responses = db.get_students_responses(request)
    questions = list(db.get_questions_by_quiz(quiz).values())

    # breakpoint()
    response = HttpResponse(content_type='application/ms-excel')

    # decide file name
    response['Content-Disposition'] = 'attachment; filename="ThePythonDjango.xls"'

    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    # adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
     # headers are bold
    font_style.font.bold = True

      # column header names, you can use your own headers here
    columns = ['Username/ID', 'Title', 'Location', 'Question', 'Chosen Option', 'Chosen Answer', 'Expected Answer', 'Correct Answer', 'Answer Submission Time', 'Answer Attempts', 'Time Spent (secs)', 'State']

    # if quiz.maxAttempts is not None:
    #     columns.append('Attempts')
    #     ws.write(row_num, 9, )

       # write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for response_obj in student_responses:
        response_json = json.loads(response_obj.response)
        for question_id in response_json:
            row_num = row_num + 1
            question = quiz.question_set.filter(pk=question_id).first()
            expected_response = question.expected_response
            student_response = response_json[question_id]
            chosen_answer = student_response[-1][0]
            if question.question_type == 'MCQ' or question.question_type == 'VMCQ':
                options = json.loads(question.options_data)
                chosen_answer = [option for option in options if option[0] == chosen_answer][0][1]
                expected_answer = [option for option in options if option[0] == expected_response][0][1]

            else:
                expected_answer = expected_response

            ws.write(row_num, 0, response_obj.user.name, font_style)
            ws.write(row_num, 1, question.question_type, font_style)
            ws.write(row_num, 2, f'{quiz.contextTitle} > {quiz.quizName} > {question.question_type}', font_style)
            ws.write(row_num, 3, question.statement, font_style)
            ws.write(row_num, 4, student_response[-1][0], font_style)
            # ws.write(row_num, 3, [option[1] for option in options if option[0] == expected_response][0], font_style)
            ws.write(row_num, 5, chosen_answer, font_style)
            ws.write(row_num, 6, expected_answer, font_style)
            ws.write(row_num, 7, 'Yes' if chosen_answer == expected_answer else 'No', font_style)
            ws.write(row_num, 8, datetime.fromtimestamp(student_response[-1][1]).strftime('%d-%m-%Y %H:%M:%S'), font_style)
            ws.write(row_num, 9, len(student_response))
            ws.write(row_num, 10, question.answer_set.first().time_spent)
            ws.write(row_num, 11, json.dumps(student_response))


    wb.save(response)
    return response
