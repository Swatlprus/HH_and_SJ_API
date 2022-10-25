import requests
from terminaltables import AsciiTable
from environs import Env

def get_superjob_stats(superjob_token):
    programm_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'Swift']
    stats = {}
    for programm_language in programm_languages:
        analysis_salary = {}
        sj_response = get_superjob_vacancies(programm_language, superjob_token)
        analysis_salary['vacancies_found']=sj_response['total']
        all_salarys = predict_rub_salary_for_superJob(sj_response['objects'])
        analysis_salary['vacancies_processed']=len(all_salarys)
        analysis_salary['average_salary']=int(sum(all_salarys)/len(all_salarys))
        stats[programm_language]=analysis_salary
    return stats

def predict_rub_salary_for_superJob(sj_vacancies):
    sj_salarys = []
    for sj_vacancy in sj_vacancies:
        if sj_vacancy['currency'] != 'rub':
            salary = None
            print('NONE')
            continue
        elif sj_vacancy['payment_from'] == 0 and sj_vacancy['payment_to'] != 0:
            salary = int(sj_vacancy['payment_to'] * 1.2)
        elif sj_vacancy['payment_from'] !=0 and sj_vacancy['payment_to'] == 0:
            salary = int(sj_vacancy['payment_from'] * 1.2)
        else:
            salary = int((sj_vacancy['payment_to'] + sj_vacancy['payment_from'])/2)
        sj_salarys.append(salary)
    return sj_salarys

def get_superjob_vacancies(programm_language, superjob_token):
    status_more = True
    page = 0
    moscow_sj_id = 4
    while status_more:
        headers = {'X-Api-App-Id': superjob_token}
        url = f'https://api.superjob.ru/2.0/vacancies/'
        params = {'keyword': programm_language, 'town': moscow_sj_id, 'page': page}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        sj_vacancies = response.json()
        if page == 0:
            all_vacancies_sj = sj_vacancies
        else:
            all_vacancies_sj['objects'].extend(sj_vacancies['objects'])
        status_more = sj_vacancies['more']
        page += 1
    return all_vacancies_sj


def get_hh_stats():
    programm_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'Swift' ]
    stats = {}
    for programm_language in programm_languages:
        analysis_salary = {}
        hh_response = get_vacancies(programm_language)
        analysis_salary['vacancies_found']=hh_response['found']
        all_salarys = predict_rub_salary_for_hh(hh_response['items'])
        analysis_salary['vacancies_processed']=len(all_salarys)
        analysis_salary['average_salary']=int(sum(all_salarys)/len(all_salarys))
        stats[programm_language]=analysis_salary
    return stats


def predict_rub_salary_for_hh(vacancies):
    salarys = []
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
            elif vacancy_salary['from'] is None and vacancy_salary['to'] is not None:
                salary = int(vacancy_salary['to'] * 1.2)
            elif vacancy_salary['from'] is not None and vacancy_salary['to'] is None:
                salary = int(vacancy_salary['from'] * 1.2)
            else:
                salary = int((vacancy_salary['to'] + vacancy_salary['from'])/2)
            salarys.append(salary)
    return salarys


def get_vacancies(programm_language):
    page = 0
    pages_number = 1
    moscow_hh_id = 1
    period = 30
    while page < pages_number:
        url = 'https://api.hh.ru/vacancies'
        params = {'text': programm_language, 'area': moscow_hh_id, 'period': period, 'search_field': 'name'}
        page_response = requests.get(url, params=params)
        page_response.raise_for_status()
        page_payload = page_response.json()
        pages_number = page_payload['pages']
        if page == 0:
            all_vacancies = page_payload
        else:
            all_vacancies['items'].extend(page_payload['items'])
        page += 1
    return all_vacancies

def get_table(stats):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата' ]]
    heading = []
    for language_stats in stats:
        heading = []
        heading.append(language_stats)
        heading.append(stats[language_stats]['vacancies_found'])
        heading.append(stats[language_stats]['vacancies_processed'])
        heading.append(stats[language_stats]['average_salary'])
        table_data.append(heading)
    return table_data

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
