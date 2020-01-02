
# Welcome to API-Toolkit!
Hi, this is a personal project. I did it for fun, to learn more about API Development, and to solve some challenges I had in my day-to-day life. 
___
### What does this API do?
This API serves two purposes:
1) Tracks personal website traffic while:
    a) Storing it in Firebase Cloud Firestore Database
    b) Sending a Pushbullet notification to my mobile device on each visit
2) Processes an incoming SMS Request from my mobile and then:
a) Computes traffic times for the input co-ordinates
b) Sends back the computed time via SMS to my mobile
___
### What was the motivation behind this project?
When I initially hosted my website, I wanted to track the number of daily visitors and filter them by geographical locations. I decided to use Google Analytics initially. However, soon I realized that this analytic engine had scattered data, and it did not satisfy my requirements.

Mobile data is also fairy expensive in Canada. For my internship, I travel 4 hours each weekday, and checking Google Maps for traffic times consumes my limited mobile data at a drastic pace. 

I knew I had to solve these problems by making my own service as the one's available on the market were either paid, or too complicated to customize.
___
### How did I do it?
I decided to solve the above 2 problems by making my own **web-analytics** engine as well as **a messaging service**. I was sure I needed a seperate back-end as I planned on integrating multiple external APIs and I did not wish to expose it on the client-side code.

I am/was also working on API Development for Canadian Imperial Bank of Commerce (CIBC) for my internship, and decided that an **API** would be the best way to tackle such problems. 

I looked at various API frameworks, such as Spring-Boot + Maven + Java, Ruby on Rails development as well as learned a little about GraphQl. 
I finally decided to make the service using **Python language** and **Flask framework**.
___

