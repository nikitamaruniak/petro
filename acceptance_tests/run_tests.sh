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

test_returns_zero_on_empty_input()
{
    input_path=$(mktemp)
    output_path=$(mktemp)
    python -m petro $input_path csv $output_path
    exit_code=$?
    rm -f $input_path $output_path
    return $exit_code
}

test_returns_2_on_errors()
{
    input_path=$(mktemp)
    echo '10 12:00:00' >> $input_path
    output_path=$(mktemp)
    python -m petro $input_path csv $output_path
    exit_code=$?
    rm -f $input_path $output_path

    if [ $exit_code -eq 2 ]
    then
        return 0
    else
        return 1
    fi
}

export PYTHONPATH=../src

failed=0

for test in $(grep -o -P 'test_.*(?=\(\))' $0)
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

