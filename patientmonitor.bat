call %USERPROFILE%\Miniconda3\condabin\activate.bat flowmeter
python %USERPROFILE%\princeton-penn-flowmeter\nursegui.py --fresh
call conda deactivate
