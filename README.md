 # HortPro Signal Notifier 
 ## Overview 
 
 HortPro Signal Notifier is a Python-based tool that scrapes presence data from the HortPro website and sends notifications via Signal when a child checks in or out of daycare. It uses Signal-CLI to send messages to individual recipients or group chats. 
 
 ## Prerequisites 
 - **Python 3.6+** 
 - **Signal-CLI** 
 must be installed and linked at `bin/signal-cli` 
 
 ## Installation 
 
 1. Clone the repository: ```bash git clone <repository-url> cd <repository-directory> ``` 
 2. Install the required Python dependencies: ```bash pip install -r requirements.txt ``` 
 3. Install Signal-CLI: - Signal-CLI is required to send messages. You can install it following the [official Signal-CLI installation documentation](https://github.com/AsamK/signal-cli/wiki/Installation). 
    - After installing, place the executable in `bin/signal-cli`: ```bash mkdir -p bin mv /path/to/signal-cli bin/signal-cli chmod +x bin/signal-cli ``` 
 4. Configure the application: - Create a configuration file (`config.json`) in the project directory with the following structure:

    ```
    {
        "signal_number": "+491234567890",
        "hortpro_login": {
            "email": "x@y.z",
            "password": "..."
        },
        "check_interval_seconds": 60
    }
    ``` 

 5. adjust `scheduler.csv` to change predefined scraping windows:

    ```
    day_of_week,start_time,end_time
    Monday,09:00,17:00
    Tuesday,09:00,17:00
    Wednesday,09:00,17:00
    Thursday,09:00,17:00
    Friday,09:00,17:00

    ```

 6. (Optional) Add recipients to receive notifications by running: 
 
    ``` bash python add_recipient.py <recipient_type> <recipient_id> ``` 

 - `<recipient_type>` can be either `individual` or `group`. 
 - `<recipient_id>` should be the phone number or Signal group ID. 

 ## Running the Application To start the notifier, run: 

    ``` bash python main.py ```

  The scraper will only run during the scheduled time windows as defined in `scheduler.csv`. 
 
 ## Logging All application logs are written to `app.log`. The log file uses a rotating handler to limit its size. 
 ## Troubleshooting
 
 1. **Unauthorized Error (401)**: - Ensure that your credentials in `config.json` are correct. - Delete the `cookie.txt` file to force a fresh login. 
 2. **Error Loading Schedule**: - Ensure `scheduler.csv` is formatted correctly and doesn't contain any comment lines or other non-CSV content. 
 3. **Signal-CLI Not Found**: - Ensure that `signal-cli` is installed in the `bin` directory and is executable. ## Additional Information 
 - For Signal-CLI installation and documentation, visit the [Signal-CLI GitHub page](https://github.com/AsamK/signal-cli). 
 - Ensure you have Java installed as Signal-CLI requires it. 
 
 ## License MIT License 

```
Copyright 2024 Nico Krebs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```