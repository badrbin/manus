from setuptools import setup, find_packages

setup(
    name="manus",
    version="0.0.1",
    description="Custom integrations and validations for ERPNext 15",
    author="Manus",
    author_email="info@manus.im",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["frappe"]
)
