call %USERPROFILE%\Miniconda3\condabin\activate.bat flowmeter
python %USERPROFILE%\princeton-penn-flowmeter\nursegui.py --debug
call conda deactivate
