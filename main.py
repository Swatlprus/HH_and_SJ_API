from cmath import exp
import requests
from terminaltables import AsciiTable
from environs import Env

def get_superjob_stats(superjob_token):
    programm_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'Swift']
    stats = {}
    for programm_language in programm_languages:
        analysis_salary = {}
        sj_response = get_superjob_vacancies(programm_language, superjob_token)
        analysis_salary['vacancies_found']=sj_response[1]
        all_salarys = predict_rub_salary_for_superJob(sj_response[0])
        analysis_salary['vacancies_processed']=len(all_salarys)
        try:
            analysis_salary['average_salary']=int(sum(all_salarys)/len(all_salarys))
        except ZeroDivisionError:
            print('Делить на ноль - нельзя. Количество найденных зарплат равно 0')
        stats[programm_language]=analysis_salary
    return stats

def calculated_salary(sj_vacancy, payment_from='payment_from', payment_to='payment_to'):
    if not sj_vacancy[payment_from] and sj_vacancy[payment_to]:
        salary = int(sj_vacancy[payment_to] * 1.2)
    elif sj_vacancy[payment_from] and not sj_vacancy[payment_to]:
        salary = int(sj_vacancy[payment_from] * 1.2)
    else:
        salary = int((sj_vacancy[payment_to] + sj_vacancy[payment_from])/2)
    return salary

def predict_rub_salary_for_superJob(sj_vacancies):
    sj_salaries = []
    for sj_vacancy in sj_vacancies:
        if sj_vacancy['currency'] != 'rub':
            salary = None
            continue
        else:
            salary = calculated_salary(sj_vacancy)
        sj_salaries.append(salary)
    return sj_salaries

def get_superjob_vacancies(programm_language, superjob_token):
    status_more = True
    page = 0
    moscow_sj_id = 4
    all_vacancies_sj = []
    while status_more:
        headers = {'X-Api-App-Id': superjob_token}
        url = f'https://api.superjob.ru/2.0/vacancies/'
        params = {'keyword': programm_language, 'town': moscow_sj_id, 'page': page}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        sj_vacancies = response.json()
        all_vacancies_sj.extend(sj_vacancies['objects'])
        status_more = sj_vacancies['more']
        page += 1
    vacancies = [all_vacancies_sj, sj_vacancies['total']]
    return vacancies


def get_hh_stats():
    programm_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'Swift' ]
    stats = {}
    for programm_language in programm_languages:
        analysis_salary = {}
        hh_response = get_vacancies(programm_language)
        analysis_salary['vacancies_found']=hh_response[1]
        all_salarys = predict_rub_salary_for_hh(hh_response[0])
        analysis_salary['vacancies_processed']=len(all_salarys)
        try:
            analysis_salary['average_salary']=int(sum(all_salarys)/len(all_salarys))
        except ZeroDivisionError:
            print('Делить на ноль - нельзя. Количество найденных зарплат равно 0')
        stats[programm_language]=analysis_salary
    return stats


def predict_rub_salary_for_hh(vacancies):
    salaries = []
    for vacancy in vacancies:
        vacancy_id = vacancy['id']
        url = f'https://api.hh.ru/vacancies/{vacancy_id}'
        response = requests.get(url)
        response.raise_for_status()
        response_text = response.json()
        vacancy_salary = response_text['salary']

        if vacancy_salary is not None:
            if vacancy_salary['currency'] != 'RUR':
                salary = None
                continue
            else:
                salary = calculated_salary(vacancy_salary, payment_from='from', payment_to='to')
            salaries.append(salary)
    return salaries


def get_vacancies(programm_language):
    page = 0
    pages_number = 1
    moscow_hh_id = 1
    period = 30
    all_vacancies = []
    while page < pages_number:
        url = 'https://api.hh.ru/vacancies'
        params = {'text': programm_language, 'area': moscow_hh_id, 'period': period, 'search_field': 'name'}
        page_response = requests.get(url, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        pages_number = page_payload['pages']
        all_vacancies.extend(page_payload['items'])
        page += 1
    vacancies = [all_vacancies, page_payload['found']]
    return vacancies

def get_table(stats):
    table_salaries_programmers = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата' ]]
    heading = []
    for language_stats in stats:
        heading = []
        heading.append(language_stats)
        heading.append(stats[language_stats]['vacancies_found'])
        heading.append(stats[language_stats]['vacancies_processed'])
        heading.append(stats[language_stats]['average_salary'])
        table_salaries_programmers.append(heading)
    return table_salaries_programmers

if __name__ == '__main__':
    env = Env()
    env.read_env()
    superjob_token = env("SUPERJOB_TOKEN")

    sj_stats = get_superjob_stats(superjob_token)
    sj_table = AsciiTable(get_table(sj_stats), 'SuperJob Moscow')
    print(sj_table.table)

    hh_stats = get_hh_stats()
    hh_table = AsciiTable(get_table(hh_stats), 'HeadHunter Moscow')
    print(hh_table.table)
