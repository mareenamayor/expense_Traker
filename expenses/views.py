from django.shortcuts import render, redirect
from django.contrib import messages
from bson import ObjectId
from config.db_connection import db
from accounts.decorators import user_login_required
from .forms import CategoryForm

@user_login_required
def category_list_view(request):
    """
    Fetches and lists all categories for the currently logged-in user.
    """
    user_id = ObjectId(request.session['user_id'])
    
    # Query MongoDB: find all category documents belonging to the user and sort by name alphabetically
    # PyMongo: find() returns a cursor, which we cast into a Python list
    categories = list(db.categories.find({'user_id': user_id}).sort('name', 1))
    
    return render(request, 'expenses/category_list.html', {'categories': categories})


@user_login_required
def category_create_view(request):
    """
    Creates a new category document.
    """
    user_id = request.session['user_id']
    
    if request.method == 'POST':
        # Pass user_id to form constructor to enable scoped name uniqueness checks
        form = CategoryForm(request.POST, user_id=user_id)
        if form.is_valid():
            name = form.cleaned_data['name']
            category_type = form.cleaned_data['type']
            color = form.cleaned_data['color']
            
            category_document = {
                'user_id': ObjectId(user_id),
                'name': name,
                'type': category_type,
                'color': color
            }
            
            # MongoDB: insert_one() writes a single document to the collection
            db.categories.insert_one(category_document)
            
            messages.success(request, f"Category '{name}' created successfully!")
            return redirect('category_list')
    else:
        form = CategoryForm(user_id=user_id)
        
    return render(request, 'expenses/category_form.html', {'form': form, 'action': 'Create'})


@user_login_required
def category_update_view(request, category_id):
    """
    Updates an existing category document after verifying user ownership.
    """
    user_id = request.session['user_id']
    
    # Convert string ID parameter from URL to BSON ObjectId
    try:
        obj_id = ObjectId(category_id)
    except Exception:
        messages.error(request, "Invalid Category ID format.")
        return redirect('category_list')
        
    # Retrieve the category document and verify ownership (Object-Level Authorization)
    category = db.categories.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not category:
        messages.error(request, "Category not found or unauthorized access.")
        return redirect('category_list')
        
    if request.method == 'POST':
        form = CategoryForm(request.POST, user_id=user_id, category_id=category_id)
        if form.is_valid():
            name = form.cleaned_data['name']
            category_type = form.cleaned_data['type']
            color = form.cleaned_data['color']
            
            # MongoDB: update_one() modifies specific fields using the $set modifier operator
            db.categories.update_one(
                {'_id': obj_id},
                {'$set': {
                    'name': name,
                    'type': category_type,
                    'color': color
                }}
            )
            
            messages.success(request, f"Category '{name}' updated successfully!")
            return redirect('category_list')
    else:
        # Pre-populate form inputs with the values fetched from MongoDB
        initial_data = {
            'name': category['name'],
            'type': category['type'],
            'color': category['color']
        }
        form = CategoryForm(initial=initial_data, user_id=user_id, category_id=category_id)
        
    return render(request, 'expenses/category_form.html', {'form': form, 'action': 'Update', 'category': category})


@user_login_required
def category_delete_view(request, category_id):
    """
    Deletes a category document. Renders confirmation page on GET, executes deletion on POST.
    """
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(category_id)
    except Exception:
        messages.error(request, "Invalid Category ID format.")
        return redirect('category_list')
        
    # Verify ownership before deletion
    category = db.categories.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not category:
        messages.error(request, "Category not found or unauthorized access.")
        return redirect('category_list')
        
    if request.method == 'POST':
        # MongoDB: delete_one() deletes the single matching document
        db.categories.delete_one({'_id': obj_id})
        messages.success(request, f"Category '{category['name']}' deleted successfully!")
        return redirect('category_list')
        
    return render(request, 'expenses/category_confirm_delete.html', {'category': category})
