Catalog Item Project
------------------------

Content

1. Project Description
2. Structure of Project Files
3. How to Run the Project
4. Credit


1. Project Description:
-----------------------

Item Catalog project is a website that used database to store the data of categories,
items, and users. The website has the following features:
	a. Display items of selected category
	b. Use third-party authentication: facebook and google for authentication and 
		authorization of changing data on the website


2. Structure of Project Files
-----------------------------

- static (directory): use to store static file such as styleset
	- styles.css: is a styleset file uses to styling the website
- templates(directory):
	- categories_admin.html: display the category with administration
			permission wich include the ability to create new 
			edit, and delete category
	- categories.html: display public page of category
	- deletecategory.html: display the confirmation of category deletion
	- deleteitem. html: display the confirmation of item deletion
	- editcategory.html: display the category edition form
	- edititem.html: display the item edition form
	- header.html: header template of website apply to all webpages
	- items.html: display public page of items
	- links.html: display important link of website
	- login_admin.html: authorization confirmation code for admin access
	- login.html: login into website as registered user
	- main.html: main template of the website
	- newcategory.html: display the new category form
	- newitem.html: display the new item form
	- viewitem.html: display the detail of item
- client_secret.json: the google developer account information
- fb_client_secret.json: the facebook developer account information
- database_setup.py: the database information and creation
- lotofitem.py: create sample items into database
- project.py: the main file of the project
- readme.txt: this file
      
3. How to Run the Project
-------------------------

Before running the code or create the tables, there will be a need to create 
database first. In this project, follow these steps in order to successfully 
run the code of the project:
   
   - Create database and tables by running: 
   		`python database_setup.py`
   - Create sample data by running:
   		`python lotofitem.py`    
   - Run the project by using command:
      	`python project.py`
   - Visit the website by `http://localhost:5000/cagetories/`
   	  for admin (the ability to add, edit, or delete categories) visit 
   	   `http://localhost:5000/categories/admin/`

4. Credit
---------

Part of the code from this project are from udacity.com lesson
   
      
      
