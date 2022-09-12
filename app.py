from flask import Flask, render_template, request, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
import os.path
import pandas as pd
import openpyxl
from glob import glob


app = Flask(__name__)
app.secret_key = "somesecretkey"


# app.config['UPLOAD_FOLDER']
app.config['MAX_CONTENT_PATH'] = 1 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = ['.csv']

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

@app.route('/', methods=['GET'])
@app.route('/upload', methods=['GET'])
def upload_file():
    return render_template('upload.html')


@app.route('/uploader', methods=['POST'])
def upload_file_1():
    if request.method == 'POST':
        f = request.files['file']
        filename = f.filename
        file_ext = os.path.splitext(filename)[1]
        full_path = os.path.join(app.root_path, UPLOAD_FOLDER)
        if file_ext in app.config['ALLOWED_EXTENSIONS']:
            flash('File uploaded successfully')
            f.save(secure_filename(f.filename))
            return  render_template('download.html', filename=filename)#filename +' -file extention should be .csv           Return to previous page'+ full_path
        return filename +' -file extention should be .csv           Return to previous page'

@app.route('/download', methods=['POST','GET'])
def downloadFile ():
    filename = glob("*.csv")[0]

    # Экспорт
    df = pd.read_csv(filename) #('Seal_data.csv')
    # Part 3. Копирование датафрейма и замена Nan на строку в типоразмере. Расчет значение
    df_new = df.copy()
    df_new['Типоразмер'] = df_new['Типоразмер'].fillna('pump model and size')
    # Замена строк (ед.измерение) на 0
    df_new.at[0,'Rated Suction Pressure'] = 0
    df_new.at[0,'Specific Gravity, rated'] = 0
    df_new.at[0,'Specific Gravity, max'] = 0
    df_new.at[0,'Differential Head, Rated'] = 0
    df_new.at[0,'TDH, shutoff'] = 0
    df_new.at[0,'Max Suction Pressure'] = 0
    # Промежуточная печать
    print(df_new['Rated Suction Pressure'], df_new['Max Suction Pressure'])
    # Преобразование строк в числа
    df_new['Rated Suction Pressure'] = df_new['Rated Suction Pressure'].astype(float)
    df_new['Max Suction Pressure'] = df_new['Max Suction Pressure'].astype(float)
    df_new['Specific Gravity, rated'] = df_new['Specific Gravity, rated'].astype(float)
    df_new['Specific Gravity, max'] = df_new['Specific Gravity, max'].astype(float)
    df_new['Differential Head, Rated'] = df_new['Differential Head, Rated'].astype(float)
    df_new['TDH, shutoff'] = df_new['TDH, shutoff'].astype(float)
    # Поиск паттернов моделей насосов, замена названия модели и расчет давлений в камере
    patternBB2 = 'RON|HVN|CGT'
    df_new.loc[df_new['Типоразмер'].str.contains(patternBB2) == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure']
    df_new.loc[df_new['Типоразмер'].str.contains(patternBB2) == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure']
    df_new.loc[df_new['Типоразмер'].str.contains(patternBB2) == True, 'Типоразмер'] = 'BB2'
    patternOH2LF = 'SCE-L'
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2LF) == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure'] + 7 * 0.00981 * df_new['Specific Gravity, rated'] * df_new['Differential Head, Rated']
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2LF) == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure'] + 7 * 0.00981 * df_new['Specific Gravity, max'] * df_new['TDH, shutoff']
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2LF) == True, 'Типоразмер'] = 'OH2LF'
    patternOH2 = 'SPI|SCE|SPN|IVP|IIL'
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2) == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure'] + 0.00981 * df_new['Specific Gravity, rated'] * df_new['Differential Head, Rated']
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2) == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure'] + 0.00981 * df_new['Specific Gravity, max'] * df_new['TDH, shutoff']
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH2) == True, 'Типоразмер'] = 'OH2'
    patternOH1 = 'CCP|CPO|IPP|CRP|SD|SK|SKO|SKV|PS|SHD|SO|GSD'
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH1) == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure'] + 0.00981 * 1.5 * (df_new['Specific Gravity, rated'] * df_new[
        'Differential Head, Rated'])
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH1) == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure'] + 0.00981 * 1.5 * (df_new['Specific Gravity, max'] * df_new['TDH, shutoff'])
    df_new.loc[df_new['Типоразмер'].str.contains(patternOH1) == True, 'Типоразмер'] = 'OH1'
    # Self prime
    df_new.loc[df_new['Типоразмер'].str.contains('SWP') == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure'] + 0.00981 * 1.5 * (df_new['Specific Gravity, rated'] * df_new[
        'Differential Head, Rated'])
    df_new.loc[df_new['Типоразмер'].str.contains('SWP') == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure'] + 0.00981 * 1.5 * (df_new['Specific Gravity, max'] * df_new['TDH, shutoff'])
    df_new.loc[df_new['Типоразмер'].str.contains('SWP') == True, 'Типоразмер'] = 'Self prime'
    # plunger
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Seal chamber pressure'] = 1.013 + df_new[
        'Rated Suction Pressure'] + 0.0981 * 1.1 * (df_new['Specific Gravity, rated'] * df_new[
        'Differential Head, Rated'])
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Max seal chamber pressure'] = 1.013 + df_new[
        'Max Suction Pressure'] + 0.0981 * 1.1 * (df_new['Specific Gravity, max'] * df_new['TDH, shutoff'])
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Типоразмер'] = 'plunger'
    # submersible
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Seal chamber pressure'] = 2.0
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Max seal chamber pressure'] = 2.0
    df_new.loc[df_new['Типоразмер'].str.contains('RDP') == True, 'Типоразмер'] = 'submersible'
    # Округление до 2-го знака после запятой
    decimals = 2
    df_new['Seal chamber pressure'] = df_new['Seal chamber pressure'].apply(lambda x: round(x, decimals))
    df_new['Max seal chamber pressure'] = df_new['Max seal chamber pressure'].apply(lambda x: round(x, decimals))

    # Part 4.импорт в excel датафрейма и печать результата
    df_new.to_excel('seal_RFQ.xlsx', sheet_name='result sheet')
    file = 'seal_RFQ.xlsx'
    xl = pd.ExcelFile(file)
    print(xl.sheet_names)
    df1 = xl.parse('result sheet')
    flash('Resuls file created successfully')

    # delete csv file using Path
    path = os.path.join(app.root_path, filename)
    # Remove the file
    os.remove(path)

    return render_template('download2.html', filename=filename)  # send_file(path, as_attachment=True)

@app.route('/download2', methods=['GET'])
def downloadFile2():
    flash('Result file <seal_RFQ.xlsx> created successfully')
    full_path = app.root_path
    filename='seal_RFQ.xlsx'

    return send_from_directory(full_path, filename, as_attachment=True)



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
