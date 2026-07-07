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
        """
        Accept custom user_id and category_id variables from views for query scoping.
        """
        self.user_id = kwargs.pop('user_id', None)
        self.category_id = kwargs.pop('category_id', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """
        Verify that a category name + type combination is unique for this specific user.
        """
        name = self.cleaned_data.get('name').strip()
        category_type = self.cleaned_data.get('type') or self.data.get('type')

        # MongoDB Query construction
        query = {
            'user_id': ObjectId(self.user_id),
            # Case-insensitive match using regex: ^ starts with, $ ends with, 'i' ignore case
            'name': {'$regex': f'^{name}$', '$options': 'i'},
            'type': category_type
        }

        # If editing, exclude the current category from the query (using MongoDB $ne - Not Equal)
        if self.category_id:
            query['_id'] = {'$ne': ObjectId(self.category_id)}

        # Execute query inside the categories collection
        if db.categories.find_one(query):
            raise forms.ValidationError(f"A {category_type} category with this name already exists in your account.")

        return name
