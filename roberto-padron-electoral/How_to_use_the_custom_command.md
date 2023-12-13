# Django custom command

This app contains a custom command that allows to load two files (separated by ' , ') to a database specified in the app settings. 

There are some important things you need to know about this command before run it.

```
You need to have the files that you want to load in the databse in the same directory where is the manage.py file 
```

```
The encoding of both files must be the same. For example: ANSI (You need to know the encoding of the files)
```

```
In the file setting.py there are some configuration about the database. Open the file and change the database engine 
for this application and add the engine that you want (mongo or postgre)
```

## Important configuration

There is a file in electoral_roll/management/commands named as load_electoral_roll.py, you need to know some aspects about it.


 ➔ There is a varible named <chunk_size> that represents the rows that you want to get from the files in each loop (Try to keep the same or greater number than the value that is setted in this variable)

### How to use the custom command?


1. Open a terminal and go to the same directory where is the manage.py file

2. In the terminal type : python manage.py load_electoral_roll <file_name_1> <file_name_2> <files_encoding> for example :
```
python manage.py load_electoral_roll electors.txt places.txt ANSI
```
3. Wait

### After run the load_electoral_roll command you must run another command to compute and load statistics in the databse. Just type the following command in the same directory that you ran the load_electoral_roll command.

```
python manage.py compute_statistics
```

## Now , something important... How could I run the django appliacation?


1. Go to the same directory where is the manage.py file

2. Open a terminal

3. Type the following command 

```
python manage.py runserver
```

4. Open a browser and go to the following address
```
 localhost:8000
```
##### Command Version 2.0