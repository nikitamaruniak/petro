test_csv_output()
{
    python -m petro test.split csv actual.csv && \
        diff actual.csv expected.csv
    exit_code=$?
    if [ $exit_code -eq 0 ]
    then
        rm actual.csv
    fi
    return $exit_code
}

test_html_output()
{
    ignore='Час створення протоколу'
    empty_line='^ *$'
    python -m petro test.split html tmp.html && \
        grep -v "$ignore" tmp.html | grep -v "$empty_line" > actual.html && \
        grep -v "$ignore" expected.html | grep -v "$empty_line" | \
        diff -w actual.html -
    exit_code=$?
    if [ $exit_code -eq 0 ]
    then
        rm actual.html tmp.html
    fi
    return $exit_code
}

export PYTHONPATH=../src

failed=0

for test in 'test_csv_output' 'test_html_output'
do
    echo "Executing test '$test'..."
    $test
    if [ $? -ne 0 ]; then
        echo 'Failed'
        let failed=$failed+1
    else
        echo 'Passed'
    fi
done

exit $failed

