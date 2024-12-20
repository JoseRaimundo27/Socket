@echo off
echo Atualizando pip...
python -m pip install --upgrade pip

echo Instalando dependências do projeto...
pip install cryptography

echo.
echo Instalação concluída. Pressione qualquer tecla para sair.
pause > nul
