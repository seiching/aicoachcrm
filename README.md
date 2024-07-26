# Line Chatbot with OpenAI ChatGPT API

This repository contains a Line chatbot application that leverages the OpenAI ChatGPT API to provide intelligent responses. The bot is designed to handle various user queries by integrating with multiple APIs and providing relevant responses.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/seiching/aicoachcrm.git
    cd aicoachcrm
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. Create a `config.ini` file in the root directory and add your configuration settings. An example `config.ini` file is provided below:
    ```ini
    [Line]
    CHANNEL_SECRET=your_channel_secret
    CHANNEL_ACCESS_TOKEN=your_channel_access_token
    [openai]
    API_KEY=your_openai_api_key
    [model]
    modelname=gpt-3.5-turbo-0125
    [ngrok]
    NGROK_AUTH_TOKEN=your_ngrok_auth_token
    [google]
    key_file=your_google_key_filename
    ```

2. Update the `config.ini` file with your actual credentials.

## Usage

1. Run the application:
    ```bash
    python app.py
    ```

2. Set up a tunnel using ngrok to expose your local server to the internet:

    ```bash

    ngrok http 5000

    ```


3. Update your Line Developer Console with the ngrok URL to receive webhook events.


5. Ensure you have a Google Drive with a worksheet named `LLMWorksheet`. The chatbot will read prompts from this worksheet to provide responses.


## File Structure

- `LICENSE`: License file.
- `README.md`: This file.
- `app.py`: Main application script.
- `config.ini`: Configuration file.
- `requirements.txt`: Python dependencies.
- `test_googleapi.py`: Unit tests for Google API integration.
- `test_linebot.py`: Unit tests for Line bot functionality.
- `test_ngrok.py`: Unit tests for ngrok integration.
- `test_openAI.py`: Unit tests for OpenAI API integration.
- `util.py`: Utility functions used across the application.

## Testing

Run the unit tests to ensure everything is working correctly:

## License
This project is licensed under the MIT License - see the LICENSE file for details.