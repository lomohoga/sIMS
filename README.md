# sIMS: *simple* inventory management system

# Requirements
* Python 3.10.x
* MySQL 8.0

# Installation
Clone this repository to your local machine. Then, create a Python virtual environment inside the local repository by running the following command through the terminal inside the directory:
```powershell
> py -m venv venv
```

After creating the virtual environment, activate it by running the following:
```powershell
> .venv/scripts/activate
```
Once the virtual environment has been activated, further terminal prompts should show `(venv)` at the beginning.

Install this project's required packages by running the following:
```powershell
> pip install requirements.txt
```

Finally, import the MySQL database dump that comes with the repository (`sims.sql`) into your machine's local MySQL connection. This may be done by selecting `Server > Data Import` after connecting through the MySQL Workbench.

# Running the application
To run the application, open the terminal in the repository's root folder, **not** the `src` folder.

Then, activate the Python virtual environment as was done during the installation.
```powershell
> ./venv/scripts/activate
```

Finally, enter the following command to run the application:
```powershell
> flask --app src run
```

The application should then be accessible in a web browser at `localhost:5000`. Do **not** close the terminal, otherwise the application will close itself.

To stop the application, press `Ctrl + C` in the terminal or close the terminal.
