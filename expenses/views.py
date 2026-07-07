import calendar
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from bson import ObjectId
from datetime import datetime, timedelta
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


# ==========================================
# DASHBOARD & REPORTS VIEWS
# ==========================================

@user_login_required
def dashboard_view(request):
    # Main dashboard view with MongoDB aggregates
    user_id = ObjectId(request.session['user_id'])
    
    # Calculate total income
    income_pipeline = [
        {'$match': {'user_id': user_id}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    income_res = list(db.income.aggregate(income_pipeline))
    total_income = income_res[0]['total'] if income_res else 0.0
    
    # Calculate total expenses
    expense_pipeline = [
        {'$match': {'user_id': user_id}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    expense_res = list(db.expenses.aggregate(expense_pipeline))
    total_expense = expense_res[0]['total'] if expense_res else 0.0
    
    # Calculate balance
    balance = total_income - total_expense
    
    # Calculate today's expenses
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    today_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {'$gte': today_start}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    today_res = list(db.expenses.aggregate(today_pipeline))
    today_expense = today_res[0]['total'] if today_res else 0.0
    
    # Fetch user categories for mapping details
    categories = db.categories.find({'user_id': user_id})
    category_map = {str(cat['_id']): cat for cat in categories}
    
    # Pie Chart data: Current month's expenses by category
    current_month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
    pie_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {'$gte': current_month_start}
        }},
        {'$group': {
            '_id': '$category_id',
            'total': {'$sum': '$amount'}
        }}
    ]
    pie_res = list(db.expenses.aggregate(pie_pipeline))
    
    pie_labels = []
    pie_data = []
    pie_colors = []
    for item in pie_res:
        cat_id_str = str(item['_id'])
        cat = category_map.get(cat_id_str, {
            'name': 'Uncategorized',
            'color': '#6c757d'
        })
        pie_labels.append(cat['name'])
        pie_data.append(float(item['total']))
        pie_colors.append(cat['color'])
        
    # Bar Chart data: Income vs Expenses for the last 6 months
    curr_year = datetime.utcnow().year
    curr_month = datetime.utcnow().month
    start_month = curr_month - 5
    start_year = curr_year
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = datetime(start_year, start_month, 1)
    
    bar_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {'$gte': start_date}
        }},
        {'$group': {
            '_id': {
                'year': {'$year': '$date'},
                'month': {'$month': '$date'}
            },
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id.year': 1, '_id.month': 1}}
    ]
    
    monthly_income_res = list(db.income.aggregate(bar_pipeline))
    monthly_expense_res = list(db.expenses.aggregate(bar_pipeline))
    
    income_map = {(r['_id']['year'], r['_id']['month']): r['total'] for r in monthly_income_res}
    expense_map = {(r['_id']['year'], r['_id']['month']): r['total'] for r in monthly_expense_res}
    
    months_list = []
    temp_year = start_year
    temp_month = start_month
    for _ in range(6):
        months_list.append((temp_year, temp_month))
        temp_month += 1
        if temp_month > 12:
            temp_month = 1
            temp_year += 1
            
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    bar_labels = []
    bar_income = []
    bar_expense = []
    
    for y, m in months_list:
        bar_labels.append(f"{month_names[m]} {y}")
        bar_income.append(float(income_map.get((y, m), 0.0)))
        bar_expense.append(float(expense_map.get((y, m), 0.0)))
        
    # Line Chart data: Daily spending trend for current month
    line_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {'$gte': current_month_start}
        }},
        {'$group': {
            '_id': {'day': {'$dayOfMonth': '$date'}},
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id.day': 1}}
    ]
    daily_expense_res = list(db.expenses.aggregate(line_pipeline))
    daily_map = {r['_id']['day']: r['total'] for r in daily_expense_res}
    
    days_in_month = calendar.monthrange(curr_year, curr_month)[1]
    line_labels = [str(d) for d in range(1, days_in_month + 1)]
    line_data = [float(daily_map.get(d, 0.0)) for d in range(1, days_in_month + 1)]
    
    # Recent Transactions list (combining last 5 income and expenses)
    recent_incomes = list(db.income.find({'user_id': user_id}).sort('date', -1).limit(5))
    recent_expenses = list(db.expenses.find({'user_id': user_id}).sort('date', -1).limit(5))
    
    for inc in recent_incomes:
        inc['type'] = 'income'
        cat_id_str = str(inc.get('category_id', ''))
        inc['category'] = category_map.get(cat_id_str, {
            'name': 'Uncategorized',
            'color': '#6c757d'
        })
        inc['amount'] = float(inc['amount'])
        
    for exp in recent_expenses:
        exp['type'] = 'expense'
        cat_id_str = str(exp.get('category_id', ''))
        exp['category'] = category_map.get(cat_id_str, {
            'name': 'Uncategorized',
            'color': '#6c757d'
        })
        exp['amount'] = float(exp['amount'])
        
    recent_transactions = sorted(recent_incomes + recent_expenses, key=lambda x: x['date'], reverse=True)[:5]
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'today_expense': today_expense,
        'recent_transactions': recent_transactions,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'pie_colors': pie_colors,
        'bar_labels': bar_labels,
        'bar_income': bar_income,
        'bar_expense': bar_expense,
        'line_labels': line_labels,
        'line_data': line_data
    }
    
    return render(request, 'expenses/dashboard.html', context)


@user_login_required
def reports_view(request):
    # View to compile custom transaction reports
    user_id = ObjectId(request.session['user_id'])
    categories = list(db.categories.find({'user_id': user_id}).sort('name', 1))
    
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    category_filter_str = request.GET.get('category', '')
    report_type = request.GET.get('report_type', 'custom')
    
    income_filter = {'user_id': user_id}
    expense_filter = {'user_id': user_id}
    
    now = datetime.utcnow()
    if report_type == 'monthly':
        start_date = datetime(now.year, now.month, 1)
        end_date = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59)
    elif report_type == 'yearly':
        start_date = datetime(now.year, 1, 1)
        end_date = datetime(now.year, 12, 31, 23, 59, 59)
    else:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime(now.year, now.month, 1) - timedelta(days=30)
            
        if end_date_str:
            end_date = datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d').date(), datetime.max.time())
        else:
            end_date = now
            
    income_filter['date'] = {'$gte': start_date, '$lte': end_date}
    expense_filter['date'] = {'$gte': start_date, '$lte': end_date}
    
    if category_filter_str:
        cat_obj_id = ObjectId(category_filter_str)
        income_filter['category_id'] = cat_obj_id
        expense_filter['category_id'] = cat_obj_id
        
    incomes = list(db.income.find(income_filter).sort('date', -1))
    expenses = list(db.expenses.find(expense_filter).sort('date', -1))
    
    total_income = sum(float(inc['amount']) for inc in incomes)
    total_expense = sum(float(exp['amount']) for exp in expenses)
    net_savings = total_income - total_expense
    
    category_map = {str(cat['_id']): cat for cat in categories}
    for inc in incomes:
        cat_id_str = str(inc.get('category_id', ''))
        inc['category'] = category_map.get(cat_id_str, {'name': 'Uncategorized', 'color': '#6c757d'})
        inc['amount'] = float(inc['amount'])
        
    for exp in expenses:
        cat_id_str = str(exp.get('category_id', ''))
        exp['category'] = category_map.get(cat_id_str, {'name': 'Uncategorized', 'color': '#6c757d'})
        exp['amount'] = float(exp['amount'])
        
    context = {
        'categories': categories,
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_category': category_filter_str,
        'report_type': report_type
    }
    
    return render(request, 'expenses/reports.html', context)
