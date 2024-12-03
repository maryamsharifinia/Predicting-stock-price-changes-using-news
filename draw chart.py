import os
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt

matplotlib.use('Agg')
import seaborn as sns

# فایل اکسل را بارگذاری کنید
file_path = r'D:\project\Predict_stock_price\results\results_فولاد1.xlsx'  # مسیر فایل اکسل خود را وارد کنید
xls = pd.ExcelFile(file_path)

# لیست شیت‌های موجود در اکسل
sheet_names = xls.sheet_names
print(sheet_names)

# استخراج مدل‌ها از اولین شیت (فرض بر این است که مدل‌ها در تمام شیت‌ها مشابه هستند)
df_first_sheet = pd.read_excel(xls, sheet_name=sheet_names[1])
models = df_first_sheet['Model'].unique()

# ایجاد نمودار
plt.figure(figsize=(10, 6))

for model in models:
    accuracies = []
    for sheet in sheet_names[1:]:
        df = pd.read_excel(xls, sheet_name=sheet)
        accuracy = df[df['Model'] == model]['Accuracy'].values[0]  # دقت مدل خاص در شیت
        accuracies.append(accuracy)
    plt.plot(sheet_names[1:], accuracies, marker='o', label=model)

# افزودن عنوان‌ها و برچسب‌ها
plt.title('Accuracy of Strategies Over Different Models')
plt.xlabel('Strategy')
plt.ylabel('Accuracy')
plt.xticks(rotation=45, ha='right')
plt.legend(title='Models')
plt.tight_layout()

# نمایش نمودار
plt.show()
plt.legend()

plt.savefig(os.path.join("models", f'فولاد.png'))
plt.close()
