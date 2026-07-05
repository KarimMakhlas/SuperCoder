def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        return "Cannot divide by zero"
    return a / b

def main():
    x = 10
    y = 0

    print("Add:", add(x, y))
    print("Subtract:", subtract(x, y))
    print("Multiply:", multiply(x, y))
    try:
        print("Divide:", divide(x, y))
    except ValueError as e:
        print("Error:", e)


if __name__ == "__main__":
    main()