mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"oburton@tellor.io\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = 443\n\
baseUrlPath = https://tellor_disputes_monitor.oraclown.repl.co\n\
[browser]\n\
serverAddress = 0.0.0.0\n\
" > ~/.streamlit/config.toml