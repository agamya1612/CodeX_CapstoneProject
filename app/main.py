from producer import submit_code

if __name__ == "__main__":
    payload = {
        "language": "python",
        "code": "print(input())",
        "input": "Hello Kafka"
    }
    submit_code(payload)