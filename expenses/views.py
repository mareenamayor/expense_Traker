from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from bson import ObjectId
from datetime import datetime
from config.db_connection import db
from accounts.decorators import user_login_required
from .forms import CategoryForm, IncomeForm, ExpenseForm

@user_login_required
def category_list_view(request):
    # Fetch and list user categories
    user_id = ObjectId(request.session['user_id'])
    categories = list(db.categories.find({'user_id': user_id}).sort('name', 1))
    return render(request, 'expenses/category_list.html', {'categories': categories})


@user_login_required
def category_create_view(request):
    # Create new category
    user_id = request.session['user_id']
    
    if request.method == 'POST':
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
            
            db.categories.insert_one(category_document)
            messages.success(request, f"Category '{name}' created successfully!")
            return redirect('category_list')
    else:
        form = CategoryForm(user_id=user_id)
        
    return render(request, 'expenses/category_form.html', {'form': form, 'action': 'Create'})


@user_login_required
def category_update_view(request, category_id):
    # Update existing category
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(category_id)
    except Exception:
        messages.error(request, "Invalid Category ID format.")
        return redirect('category_list')
        
    # Get category and verify ownership
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
        initial_data = {
            'name': category['name'],
            'type': category['type'],
            'color': category['color']
        }
        form = CategoryForm(initial=initial_data, user_id=user_id, category_id=category_id)
        
    return render(request, 'expenses/category_form.html', {'form': form, 'action': 'Update', 'category': category})


@user_login_required
def category_delete_view(request, category_id):
    # Delete category view
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(category_id)
    except Exception:
        messages.error(request, "Invalid Category ID format.")
        return redirect('category_list')
        
    category = db.categories.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not category:
        messages.error(request, "Category not found or unauthorized access.")
        return redirect('category_list')
        
    if request.method == 'POST':
        db.categories.delete_one({'_id': obj_id})
        messages.success(request, f"Category '{category['name']}' deleted successfully!")
        return redirect('category_list')
        
    return render(request, 'expenses/category_confirm_delete.html', {'category': category})


# ==========================================
# INCOME MANAGEMENT VIEWS
# ==========================================

@user_login_required
def income_list_view(request):
    # List all income with search and pagination
    user_id = ObjectId(request.session['user_id'])
    query_param = request.GET.get('q', '').strip()
    
    search_filter = {'user_id': user_id}
    
    # Filter by search query if present
    if query_param:
        search_filter['$or'] = [
            {'source': {'$regex': query_param, '$options': 'i'}},
            {'description': {'$regex': query_param, '$options': 'i'}}
        ]
        
    incomes = list(db.income.find(search_filter).sort('date', -1))
    
    # Get user categories for mapping
    categories = db.categories.find({'user_id': user_id})
    category_map = {str(cat['_id']): cat for cat in categories}
    
    for inc in incomes:
        cat_id_str = str(inc.get('category_id', ''))
        inc['category'] = category_map.get(cat_id_str, {
            'name': 'Uncategorized',
            'color': '#6c757d'
        })
        inc['amount'] = float(inc['amount'])
        
    # Paginate results
    paginator = Paginator(incomes, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'expenses/income_list.html', {
        'page_obj': page_obj,
        'query': query_param
    })


@user_login_required
def income_create_view(request):
    # Add new income record
    user_id = request.session['user_id']
    
    if request.method == 'POST':
        form = IncomeForm(request.POST, user_id=user_id)
        if form.is_valid():
            amount = float(form.cleaned_data['amount'])
            source = form.cleaned_data['source']
            category_id = form.cleaned_data['category']
            date_val = form.cleaned_data['date']
            description = form.cleaned_data['description']
            
            date_dt = datetime.combine(date_val, datetime.min.time())
            
            income_document = {
                'user_id': ObjectId(user_id),
                'category_id': ObjectId(category_id) if category_id else None,
                'amount': amount,
                'source': source,
                'date': date_dt,
                'description': description,
                'created_at': datetime.utcnow()
            }
            
            db.income.insert_one(income_document)
            messages.success(request, f"Income of ${amount:.2f} added successfully!")
            return redirect('income_list')
    else:
        form = IncomeForm(user_id=user_id)
        
    return render(request, 'expenses/income_form.html', {'form': form, 'action': 'Add'})


@user_login_required
def income_update_view(request, income_id):
    # Update existing income record
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(income_id)
    except Exception:
        messages.error(request, "Invalid Income ID format.")
        return redirect('income_list')
        
    income = db.income.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not income:
        messages.error(request, "Income record not found or unauthorized access.")
        return redirect('income_list')
        
    if request.method == 'POST':
        form = IncomeForm(request.POST, user_id=user_id)
        if form.is_valid():
            amount = float(form.cleaned_data['amount'])
            source = form.cleaned_data['source']
            category_id = form.cleaned_data['category']
            date_val = form.cleaned_data['date']
            description = form.cleaned_data['description']
            
            date_dt = datetime.combine(date_val, datetime.min.time())
            
            db.income.update_one(
                {'_id': obj_id},
                {'$set': {
                    'category_id': ObjectId(category_id) if category_id else None,
                    'amount': amount,
                    'source': source,
                    'date': date_dt,
                    'description': description
                }}
            )
            
            messages.success(request, "Income record updated successfully!")
            return redirect('income_list')
    else:
        initial_data = {
            'amount': income['amount'],
            'source': income['source'],
            'category': str(income['category_id']) if income.get('category_id') else '',
            'date': income['date'].date() if isinstance(income['date'], datetime) else income['date'],
            'description': income['description']
        }
        form = IncomeForm(initial=initial_data, user_id=user_id)
        
    return render(request, 'expenses/income_form.html', {'form': form, 'action': 'Edit', 'income': income})


@user_login_required
def income_delete_view(request, income_id):
    # Delete income record
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(income_id)
    except Exception:
        messages.error(request, "Invalid Income ID format.")
        return redirect('income_list')
        
    income = db.income.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not income:
        messages.error(request, "Income record not found or unauthorized access.")
        return redirect('income_list')
        
    if request.method == 'POST':
        db.income.delete_one({'_id': obj_id})
        messages.success(request, "Income record deleted successfully!")
        return redirect('income_list')
        
    return render(request, 'expenses/income_confirm_delete.html', {'income': income})


# ==========================================
# EXPENSE MANAGEMENT VIEWS
# ==========================================

@user_login_required
def expense_list_view(request):
    # List all expenses with search and pagination
    user_id = ObjectId(request.session['user_id'])
    query_param = request.GET.get('q', '').strip()
    
    search_filter = {'user_id': user_id}
    
    if query_param:
        search_filter['$or'] = [
            {'payee': {'$regex': query_param, '$options': 'i'}},
            {'description': {'$regex': query_param, '$options': 'i'}}
        ]
        
    expenses = list(db.expenses.find(search_filter).sort('date', -1))
    
    # Get user categories for mapping
    categories = db.categories.find({'user_id': user_id})
    category_map = {str(cat['_id']): cat for cat in categories}
    
    for exp in expenses:
        cat_id_str = str(exp.get('category_id', ''))
        exp['category'] = category_map.get(cat_id_str, {
            'name': 'Uncategorized',
            'color': '#6c757d'
        })
        exp['amount'] = float(exp['amount'])
        
    # Paginate results
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'expenses/expense_list.html', {
        'page_obj': page_obj,
        'query': query_param
    })


@user_login_required
def expense_create_view(request):
    # Add new expense record
    user_id = request.session['user_id']
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user_id=user_id)
        if form.is_valid():
            amount = float(form.cleaned_data['amount'])
            payee = form.cleaned_data['payee']
            category_id = form.cleaned_data['category']
            date_val = form.cleaned_data['date']
            description = form.cleaned_data['description']
            
            date_dt = datetime.combine(date_val, datetime.min.time())
            
            expense_document = {
                'user_id': ObjectId(user_id),
                'category_id': ObjectId(category_id) if category_id else None,
                'amount': amount,
                'payee': payee,
                'date': date_dt,
                'description': description,
                'created_at': datetime.utcnow()
            }
            
            db.expenses.insert_one(expense_document)
            messages.success(request, f"Expense of ${amount:.2f} to '{payee}' added successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm(user_id=user_id)
        
    return render(request, 'expenses/expense_form.html', {'form': form, 'action': 'Add'})


@user_login_required
def expense_update_view(request, expense_id):
    # Update existing expense record
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(expense_id)
    except Exception:
        messages.error(request, "Invalid Expense ID format.")
        return redirect('expense_list')
        
    expense = db.expenses.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not expense:
        messages.error(request, "Expense record not found or unauthorized access.")
        return redirect('expense_list')
        
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user_id=user_id)
        if form.is_valid():
            amount = float(form.cleaned_data['amount'])
            payee = form.cleaned_data['payee']
            category_id = form.cleaned_data['category']
            date_val = form.cleaned_data['date']
            description = form.cleaned_data['description']
            
            date_dt = datetime.combine(date_val, datetime.min.time())
            
            db.expenses.update_one(
                {'_id': obj_id},
                {'$set': {
                    'category_id': ObjectId(category_id) if category_id else None,
                    'amount': amount,
                    'payee': payee,
                    'date': date_dt,
                    'description': description
                }}
            )
            
            messages.success(request, "Expense record updated successfully!")
            return redirect('expense_list')
    else:
        initial_data = {
            'amount': expense['amount'],
            'payee': expense['payee'],
            'category': str(expense['category_id']) if expense.get('category_id') else '',
            'date': expense['date'].date() if isinstance(expense['date'], datetime) else expense['date'],
            'description': expense['description']
        }
        form = ExpenseForm(initial=initial_data, user_id=user_id)
        
    return render(request, 'expenses/expense_form.html', {'form': form, 'action': 'Edit', 'expense': expense})


@user_login_required
def expense_delete_view(request, expense_id):
    # Delete expense record
    user_id = request.session['user_id']
    
    try:
        obj_id = ObjectId(expense_id)
    except Exception:
        messages.error(request, "Invalid Expense ID format.")
        return redirect('expense_list')
        
    expense = db.expenses.find_one({'_id': obj_id, 'user_id': ObjectId(user_id)})
    if not expense:
        messages.error(request, "Expense record not found or unauthorized access.")
        return redirect('expense_list')
        
    if request.method == 'POST':
        db.expenses.delete_one({'_id': obj_id})
        messages.success(request, "Expense record deleted successfully!")
        return redirect('expense_list')
        
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})
