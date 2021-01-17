# finance

attention beforehand, if you want to try this application use the CS50 IDE!

Configuring
Before getting started on this assignment, we’ll need to register for an API key in order to be able to query IEX’s data. To do so, follow these steps:

Visit iexcloud.io/cloud-login#/register/.
1. Enter your email address and a password, and click “Create account”.
2. On the next page, scroll down to choose the Start (free) plan.
3. Once you’ve confirmed your account via a confirmation email, sign in to iexcloud.io.
4. Click API Tokens.
5. Copy the key that appears under the Token column (it should begin with pk_).
6. In a terminal window within CS50 IDE, execute:

  $ export API_KEY=value
  
where value is that (pasted) value, without any space immediately before or after the =. You also may wish to paste that value in a text document somewhere, in case you need it again later.

7. Start Flask’s built-in web server (within finance/):
  
  $ flask run
