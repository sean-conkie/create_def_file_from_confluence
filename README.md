<h2>Setup</h2>

Run setup.bat, this will create a virtual environment for the code to run (not mandatory but isolates it from possible conflicts) and install the dependencies.

Alternative setup, run python -m pip install -r .\requirements.txt to install dependencies to main env.

<h2>How to Use</h2>

activate virtual environment by running .\def-file-venv\Scripts\activate
You can then create def file via cmd/ps using; 
```batch 
python .\deffile.py <url> email=<your email> headless=<True/False>
```

or running the following

```batch
python
```
then
```python
from deffile import 

createdef(<url>,<email>,<headless>)
```

email (optional) is your email address for signing in to confluence

headless (optional) controls if the browser is displayed

<h2>Unable to run scripts?</h2>
run;

```PowerShell
Set-ExecutionPolicy Unrestricted -Scope Process
```