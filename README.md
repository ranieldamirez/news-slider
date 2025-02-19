# news-slider; https://news-slider.onrender.com/

## A hobby-project; creating a website/app that will allow to user to view various news sources based on their political leanings. Currently deployed and hosted on www.render.com.

### **For local deployment:**

You will need to make your own API key in https://newsapi.org/ and save it to a .env file in the project directory. In the .env file, you should write 
``` .env
"NEWSAPI_KEY=Insert_API_key_here"
```

#### How to Run
1) run 'fetch_headlines.py'
2) run 'app.py'
3) visit http://127.0.0.1:5000/headlines to see a json of all the files

# TO-DO:
- make the website look pretty
- incoporate filters based on topics
