import gkeepapi
from tqdm import tqdm
import json

from nordestao import search_term


def login(email, password):
    keep = gkeepapi.Keep()
    success = keep.login(email, password)
    if not success:
        print("Falha no login")
        exit(1)
    return keep


def get_list(keep, list_id):
    # Pegando a lista de compras
    shopping_list = keep.get(list_id)
    list_items = shopping_list.items
    # Caso não existam items na lista
    if list_items == []:
        print("Nenhum item na lista")
        exit(1)
    # Removendo antigo total estimado da lista
    for item in list_items:
        if "R$" in item.text:
            item.delete()
            list_items.remove(item)

    return shopping_list, list_items


def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
        if "email" not in config or "password" not in config or "list_id" not in config:
            print("Falta email, senha ou id da lista no arquivo config.json")
            exit(1)
    return config


def main():
    # Pegando dados de login
    config = load_config()
    # Login
    keep = login(config["email"], config["password"])
    print("Login efetuado com sucesso")

    # Pegando os items da lista
    shopping_list, list_items = get_list(keep, config["list_id"])
    print("Lista de compras carregada")

    # Adicionando novo total estimado da lista
    total_price = 0
    items = []

    # Iterando sobre os items da lista e buscando o preço
    print("Iniciando busca de preços...")

    for item in tqdm(list_items):
        # Verifica se o item tem um numero e espaço no começo, caso tenha adicione o valor do item vezes  o numero no início
        if item.text[0].isdigit() and item.text[1] == " ":
            quantity = int(item.text[0])
            item_name = item.text[2:]
        else:
            item_name = item.text
            quantity = 1

        # Usando api do Nordestão para pegar o preço do item
        nordestao_item = search_term(item_name, quantity)
        total_price += float(nordestao_item.get("total"))
        items.append(nordestao_item)

    print("Busca de preços finalizada")

    # Criando um log dos itens em um arquivo json
    with open("./logs/items.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=2))
    print("Log dos itens criado")

    # Adicionando novo total estimado da lista
    total_price = round(total_price)
    shopping_list.add(f"Total estimado: R$ {total_price}", True)
    print("Total estimado adicionado na lista")

    # Sincronizando com o Google Keep
    keep.sync()
    print("Sincronização com o Google Keep finalizada")
    # Imprimindo o total estimado da lista
    print(f"Total estimado: R$ {total_price}")
    print(
        f"Lista de compras atualizada: https://keep.google.com/u/0/#LIST/{config['list_id']}")


main()
