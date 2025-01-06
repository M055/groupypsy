import pandas as pd
import os
import numpy as np
from pulp import *
import re
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('agg')

def process_csv_files(file_paths, session_id):
    output_path = os.path.join('static', 'download', f"Assignments_{session_id}.csv")
    plot_path = os.path.join('static', 'plots', f"plot_{session_id}.png") 
    # OLDER::>  output_path = "static/download/processed_output.csv"

    # Example: Reading multiple CSVs
    # dfs = {file_name: pd.read_csv(file_path) for file_name, file_path in file_paths.items()}
    # Perform processing...
    # combined_df = pd.concat(dfs.values())
    # combined_df.to_csv(output_path, index=False)


    ###### 2 READ DATA
    for file_name, file_path in file_paths.items():
        if 'student' in file_name:
            studentsdf = pd.read_csv(file_path,index_col=0) 
        if 'project' in file_name:
            projectsdf = pd.read_csv(file_path,index_col=0)
        if 'requirement' in file_name: 
            reqsdf = pd.read_csv(file_path,index_col=0) 
        if 'choice' in file_name:
            choicedf = pd.read_csv(file_path,index_col=0)        
    
    
    

    choice_matrix_flag = 1 if ((choicedf.shape[0] == len(studentsdf)) & (choicedf.shape[1] == len(projectsdf))) else 0

    students = studentsdf.index.tolist()
    projects = projectsdf.index.tolist()
    requirements = reqsdf.index.tolist()
    # TODO: Usxe the lists above for below

    #Summarize the data
    check_mesg_1 = f" There are {len(projectsdf)} projects with {len(reqsdf)} requirements. There are a total of {projectsdf.Capacity.sum()} slots available across all projects."
    check_mesg_2 = f" There are {len(studentsdf)} students, and the choice matrix {'is correct.' if choice_matrix_flag else 'needs fixing!'}"
    print(check_mesg_1)
    print(check_mesg_2)
    check_mesg = check_mesg_1 + check_mesg_2




    ###### 3 Assertions to ensure data quality
    assert(projectsdf.index.tolist()==choicedf.columns.tolist())
    assert(studentsdf.index.tolist()==choicedf.index.tolist())



    ###### 4. Format variables, create dictionaries
    # Create ranking matrix dictionary
    ranking_matrix = choicedf.to_dict('index')

    # Project capacities
    project_capacities = dict([(x,y) for x,y in zip(projectsdf.index.tolist(),projectsdf['Capacity'])])

    # Create dictionaries for student qualifications and project requirements
    student_qualifications_dict = studentsdf.loc[:,[x for x in studentsdf.columns if 'Requirement' in x]].to_dict("index")
    project_requirements_dict = projectsdf.loc[:,[x for x in projectsdf.columns if 'Requirement' in x]].to_dict("index")

    # TEST: Only a single requirement:
    # student_qualifications_dict = studentsdf.loc[:,[x for x in studentsdf.columns if 'Requirement_01' in x]].to_dict("index")
    # project_requirements_dict = projectsdf.loc[:,[x for x in projectsdf.columns if 'Requirement_01' in x]].to_dict("index")



    ###### 5. Create PuLP model and add constraints
    # Create a PuLP problem
    model = LpProblem("StudentProjectAssignment", LpMinimize)

    # Create decision variables: 1 if student i is assigned to project j, 0 otherwise
    x = LpVariable.dicts("assign", (students, projects), 0, 1, LpInteger)

    # Objective: Minimize the sum of rankings for assigned projects
    model += lpSum(ranking_matrix[student][project] * x[student][project] for student in students for project in projects)


    # Constraints:
    # Each student can be assigned to only one project
    for student in students:
        model += lpSum(x[student][project] for project in projects) == 1

    # Each project's capacity not exceeded
    for project in projects:
        model += lpSum(x[student][project] for student in students) <= project_capacities[project]



    # Add the constraint that a student can only be assigned to a project if they meet all the required requirements for that project
    for student in students:
        for project in projects:
            for req, required in project_requirements_dict[project].items():
                if required == 1:  # Only care about required requirements
                    # Student must meet the requirement for the project
                    model += x[student][project] <= student_qualifications_dict[student].get(req, 0), f"Requirement_{req}_for_{student}_on_{project}"


    # Solve the model
    model.solve()



    ##### 6. Gather and format the output
    assignmentsdf = pd.DataFrame()
    for v in model.variables():
        if v.value() == 1:
            var_name = str(v.name)
            this_student, this_project = re.search("Student_(\d+)", var_name).group(), re.search("Project_(\d+)", var_name).group()
            
            # FOr this student, get the rank for this project num
            this_rank = choicedf.loc[choicedf.index==this_student,choicedf.columns==this_project].values[0][0]

            
            
            # Find the requirememts for this project, see if student has them all
            this_proj_reqs = projectsdf.loc[projectsdf.index==this_project,requirements]
            this_stud_reqs = studentsdf.loc[studentsdf.index==this_student,requirements]

            # NExt 2, TEST for single requirement
            this_proj_reqs = projectsdf.loc[projectsdf.index==this_project,requirements[0]]
            this_stud_reqs = studentsdf.loc[studentsdf.index==this_student,requirements[0]]

            
            reqs_met = 1 if np.all((this_proj_reqs.values[0]*this_stud_reqs.values[0])==this_proj_reqs.values[0]) else 0
            assignmentsdf = pd.concat((assignmentsdf,pd.DataFrame({'StudentNum':this_student, 'ProjectNum':this_project, 'RankChoice':this_rank, 'RequirementsMet':reqs_met},index=[0])))
            
    assignmentsdf.reset_index(drop=True, inplace=True)
    # assignmentsdf.head()
    assignmentsdf.to_csv(output_path, index=False) # SAVE
 

    ##### FIGURE
    MAX_X = len(projectsdf) # Can have only so many choices
    NUM_REQS = len(reqsdf) # So many requirements
    sns.histplot(assignmentsdf.RankChoice, discrete=True, cumulative=True, stat='percent',linewidth=3, edgecolor='r')
    plt.plot([0, MAX_X+0.5],[90, 90],'r:', linewidth=1)
    plt.gca().grid(True, linestyle=':', linewidth=1)  # Set dotted gridlines
    plt.gca().set_xticks(range(MAX_X))
    plt.gca().set_xlim([0, MAX_X+0.5])
    plt.title(f'{str(NUM_REQS)} requirement(s); '+str(MAX_X)+' projects')
    plt.ylabel("% getting <= (rank) choice")
    plt.savefig(plot_path)
    plt.close()


    return output_path, plot_path, list(assignmentsdf.columns), check_mesg

