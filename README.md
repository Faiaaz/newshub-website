# NewsHub - News Website

A modern news website built with Flask, featuring a clean design inspired by traditional news sites like Bangla Outlook.

## Features

- 📰 **News Articles**: Create, edit, and manage news articles
- 🎨 **Clean Design**: Professional, responsive design
- 📱 **Mobile Friendly**: Works great on all devices
- 🔍 **Search & Filter**: Search articles and filter by categories
- 🏷️ **Tags System**: Organize articles with tags
- 👤 **Admin Panel**: Full admin interface for content management
- 🖼️ **Image Upload**: Support for article images
- 📊 **PostgreSQL Database**: Robust data storage

## Tech Stack

- **Backend**: Flask, Python
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS (inspired by Bangla Outlook)
- **Deployment**: Railway/Render ready

## Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd news_site2
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   createdb news_db
   ```

5. **Create .env file**
   ```
   DATABASE_URL=postgresql://postgres:1234d@localhost:5432/news_db
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the website**
   - Main site: http://127.0.0.1:8080
   - Admin panel: http://127.0.0.1:8080/admin/login
   - Admin credentials: admin / admin123

## Deployment

### Railway (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Railway**
   - Go to [Railway](https://railway.app/)
   - Connect your GitHub account
   - Create new project from GitHub repo
   - Add PostgreSQL database
   - Deploy!

### Environment Variables

Set these in your hosting platform:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key (generate a secure one)

## Admin Panel

- **URL**: `/admin/login`
- **Username**: admin
- **Password**: admin123

## Project Structure

```
news_site2/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version
├── templates/            # HTML templates
│   ├── index.html        # Homepage
│   ├── article.html      # Article detail page
│   └── admin/           # Admin templates
├── static/              # Static files
│   └── uploads/         # Uploaded images
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License. 