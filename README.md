# Python - Streamlit

This is a simple Python - Streamlit application. This application serves as a basic template for building interactive web applications using Python and Streamlit framework.

Visit [Streamlit Documentation](https://docs.streamlit.io/) for more information.

## What does this application do?

This application serves a simple interactive web interface that listens on defined port, default: `8080`.

# How to run?

You can run the application in one of the following ways:

1. Press `F5`. This will start the application in development mode.

2. Open a terminal by going to 'View' -> 'Terminal'. Then, run following command:
   > `streamlit run app.py --server.port=8080 --server.address=0.0.0.0`

This will start the application and you can access it in your browser.

## Via curl command:

1. Open a terminal.
2. Type the following command:
   > `curl http://localhost:8080`
3. Press 'Enter' to make the request.

## FAQs & Debugging

### 1. I do not see browser in my workspace

Studio will automatically open the app in a new browser tab. If not, you can use the following steps to open the simple browser:

1. From VS Code command palette (`Ctrl/Cmd + Shift + P`), run **Studio Manager: SimpleBrowser Default URL** command. This will open the app in a new browser tab.

2. Your app runs on a hosted environment which can be accessed using the host id and port provided in the file **.vscode/.studio/studio-env.json**. Use these values to create the URL as follows:
   `https://<STUDIO_HOST_ID>-8080.<STUDIO_DOMAIN>`


Happy coding!
