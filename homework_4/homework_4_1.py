class Product:
    def __init__(self, name, category, price, quantity):
        self.name = name
        self.category = category
        self.price = float(price)
        self.quantity = int(quantity)

    def change_price(self, new_price):
        self.price = float(new_price)

    def change_quantity(self, new_quantity):
        self.quantity = int(new_quantity)


class Order:
    def __init__(self):
        self.products = []
        self.total = 0

    def add_product(self, product, quantity):
        if product.quantity >= quantity:
            self.products.append((product, quantity))
            product.quantity -= quantity

    def calculate_total(self):
        self.total = 0
        for product, quantity in self.products:
            self.total += product.price * quantity
        return self.total


class Customer:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)


products = []

with open("products.txt", "r", encoding="utf-8") as file:
    for line in file:
        name, category, price, quantity = line.strip().split(",")
        products.append(Product(name, category, price, quantity))


customers = []

with open("customers.txt", "r", encoding="utf-8") as file:
    for line in file:
        name, email = line.strip().split(",")
        customers.append(Customer(name, email))


order = Order()
order.add_product(products[0], 2)
order.add_product(products[1], 1)

customers[0].add_order(order)

print(order.calculate_total())