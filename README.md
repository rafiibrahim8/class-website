[![License][License-shield]][License-url]

# class-website

#### A website for managing my class stuffs.


# INSTALLATION

Install `nginx`
```bash
sudo apt install nginx-light
```
Clone the repo
```bash
git clone https://github.com/rafiibrahim8/class-website.git
cd class-website
```
Install dependencies
```bash
pip install -r requirements.txt
```
Unzip static files
```bash
sudo mkdir -p /var/www/static/.theme
sudo unzip -d /var/www/static/.theme nginx-files/class-website.zip 
```
Configure nginx
```bash
echo '127.0.0.1  class-website.local' | sudo tee -a /etc/hosts
sudo cp nginx-files/reverse-proxy.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/reverse-proxy.conf /etc/nginx/sites-enabled/reverse-proxy.conf
sudo systemctl restart nginx
```
Run the server
```bash
gunicorn --bind 127.0.0.1:65005 wsgi:app
```
Your shoud see the website at: [http://class-website.local](http://class-website.local)

# ISSUES

This is very early stage of the program. It might be very buggy. You are always welcome to [create an issue](https://github.com/rafiibrahim8/class-website/issues) or [submit a pull request](https://github.com/rafiibrahim8/class-website/pulls).

[License-shield]: https://img.shields.io/github/license/rafiibrahim8/class-website
[License-url]: https://github.com/rafiibrahim8/class-website/blob/master/LICENSE

