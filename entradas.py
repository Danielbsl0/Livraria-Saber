def solicitar_id(mensagem):
    """Solicita um ID e aceita somente números inteiros positivos."""
    while True:
        valor = input(mensagem).strip()
        try:
            identificador = int(valor)
            if identificador > 0:
                return identificador
        except ValueError:
            pass

        print("Informe um ID numérico positivo.")
