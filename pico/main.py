from wifi import connect


def main():
    wlan = connect()
    print("Ready, IP:", wlan.ifconfig()[0])


if __name__ == "__main__":
    main()