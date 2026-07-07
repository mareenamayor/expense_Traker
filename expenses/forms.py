from django import forms
from config.db_connection import db
from bson import ObjectId

class CategoryForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'})
    )
    type = forms.ChoiceField(
        choices=[('income', 'Income'), ('expense', 'Expense')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    color = forms.CharField(
        max_length=7,
        initial='#4a4e69',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-color w-100', 'type': 'color', 'style': 'height: 40px;'})
    )

    def __init__(self, *args, **kwargs):
        # Accept user_id and category_id variables
        self.user_id = kwargs.pop('user_id', None)
        self.category_id = kwargs.pop('category_id', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        # Verify unique category name per user
        name = self.cleaned_data.get('name').strip()
        category_type = self.cleaned_data.get('type') or self.data.get('type')

        # Find duplicates in database
        query = {
            'user_id': ObjectId(self.user_id),
            'name': {'$regex': f'^{name}$', '$options': 'i'},
            'type': category_type
        }

        # Exclude current category if editing
        if self.category_id:
            query['_id'] = {'$ne': ObjectId(self.category_id)}

        # Raise error if match found
        if db.categories.find_one(query):
            raise forms.ValidationError(f"A {category_type} category with this name already exists in your account.")

        return name


class IncomeForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'})
    )
    source = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Salary, Freelance'})
    )
    category = forms.ChoiceField(
        choices=[], # Populated in init
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Optional details...', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        # Populate income categories
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        
        # Fetch user's income categories
        if user_id:
            categories = db.categories.find({
                'user_id': ObjectId(user_id),
                'type': 'income'
            }).sort('name', 1)
            
            # Map to choice format
            category_choices = [(str(cat['_id']), cat['name']) for cat in categories]
            
            # Default choice if list is empty
            if not category_choices:
                category_choices = [('', '-- Create a category first --')]
                
            self.fields['category'].choices = category_choices


class ExpenseForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'})
    )
    payee = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Supermarket, Landlord'})
    )
    category = forms.ChoiceField(
        choices=[], # Populated in init
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Optional details...', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        # Populate expense categories
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        
        # Fetch user's expense categories
        if user_id:
            categories = db.categories.find({
                'user_id': ObjectId(user_id),
                'type': 'expense'
            }).sort('name', 1)
            
            # Map to choice format
            category_choices = [(str(cat['_id']), cat['name']) for cat in categories]
            
            # Default choice if list is empty
            if not category_choices:
                category_choices = [('', '-- Create a category first --')]
                
            self.fields['category'].choices = category_choices
