# Changelog

## Version 1.0.8 - 2022-09-13
- For the model view, use the code env that was used to train the model
  - The model view can now be used for both Python 2 and Python 3 models
- Avoid to load external resources (use a minified file for AngularJS...)
- Remove use of jQuery
- Clean unused code (Surrogate model...)
- Only display model view for binary classification, multiclass or regression models, using a Python backend
