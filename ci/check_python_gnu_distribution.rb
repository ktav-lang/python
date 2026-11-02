require 'yaml'

# Точные source/CPU/resource gates shared GNU producer.
def validate_python_gnu_contract(native, gnu)
  call = native.fetch('jobs').fetch('windows-gnu')
  raise 'wrong GNU caller' unless call.fetch('uses') == './.github/workflows/windows-gnu-pyo3-probe.yml'
  raise 'GNU source is not forwarded' unless call.fetch('with').fetch('source-ref') == '${{ inputs.source-ref }}'
  triggers = gnu['on'] || gnu[true]
  raise 'missing GNU source contract' unless triggers.fetch('workflow_call').fetch('inputs').fetch('source-ref').fetch('required')
  raise 'duplicate standalone GNU producer' if triggers.key?('pull_request')
  raise 'GNU source environment ignores caller' unless gnu.fetch('env').fetch('SOURCE_REF').include?('inputs.source-ref')
  job = gnu.fetch('jobs').fetch('compatibility')
  actual = job.fetch('strategy').fetch('matrix').fetch('include').map do |item|
    [item.fetch('os'), item.fetch('target'), item.fetch('label'), item.fetch('python-arch'), item.fetch('python-version')]
  end
  expected = [
    ['windows-latest', 'x86_64-pc-windows-gnullvm', 'windows-x86_64', 'x64', '3.13.16'],
    ['windows-11-arm', 'aarch64-pc-windows-gnullvm', 'windows-aarch64', 'arm64', '3.13.17'],
  ]
  raise 'wrong genuine CPU/source-library matrix' unless actual.sort == expected.sort
  steps = job.fetch('steps')
  required = [
    'Bind original Python source and dependency identities',
    'Install exact SDK and bind real matching-CPU CPython import libraries',
    'Prepare complete source-bound Python GNU and CPython original grants',
    'Inspect actual PE and run unchanged original native Python tests',
    'Verify complete actual wheel and exact retained-input/source-grant binding',
  ]
  required.each do |name|
    step = steps.find { |item| item['name'] == name }
    raise "missing mandatory GNU gate #{name}" unless step && !step.key?('if') && !step['continue-on-error']
  end
  uploads = steps.select { |item| item['uses'].to_s.start_with?('actions/upload-artifact@') }
  wheels = uploads.select { |item| item.fetch('with').fetch('name').start_with?('wheels-') }
  raise 'wrong GNU native release role' unless wheels.length == 1 && wheels[0].fetch('with').fetch('name') == 'wheels-native-${{ matrix.label }}' && wheels[0].fetch('with').fetch('path').end_with?('/*.whl') && !wheels[0].key?('if') && !wheels[0]['continue-on-error']
  verify_index = steps.index { |item| item['name'] == required[-1] }
  raise 'wheel upload precedes complete source/grant acceptance' unless verify_index < steps.index(wheels[0])
  true
end

native = YAML.load_file('.github/workflows/native-release-build.yml')
gnu = YAML.load_file('.github/workflows/windows-gnu-pyo3-probe.yml')
validate_python_gnu_contract(native, gnu)
mutations = [
  ->(n, _) { n.fetch('jobs').fetch('windows-gnu').fetch('with')['source-ref'] = 'unreviewed' },
  ->(_, g) { (g['on'] || g[true]).fetch('workflow_call').fetch('inputs').fetch('source-ref')['required'] = false },
  ->(_, g) { g.fetch('jobs').fetch('compatibility').fetch('strategy').fetch('matrix').fetch('include')[1]['os'] = 'windows-latest' },
  ->(_, g) { g.fetch('jobs').fetch('compatibility').fetch('strategy').fetch('matrix').fetch('include')[0]['python-version'] = '3.13' },
  ->(_, g) { g.fetch('jobs').fetch('compatibility').fetch('steps').find { |s| s['name'] == 'Prepare complete source-bound Python GNU and CPython original grants' }['continue-on-error'] = true },
  ->(_, g) { g.fetch('jobs').fetch('compatibility').fetch('steps').find { |s| s['name'] == 'Verify complete actual wheel and exact retained-input/source-grant binding' }['if'] = 'false' },
  ->(_, g) { g.fetch('jobs').fetch('compatibility').fetch('steps').find { |s| s.dig('with', 'name') == 'wheels-native-${{ matrix.label }}' }['if'] = 'always()' },
]
mutations.each_with_index do |mutation, index|
  n = Marshal.load(Marshal.dump(native))
  g = Marshal.load(Marshal.dump(gnu))
  mutation.call(n, g)
  rejected = false
  begin
    validate_python_gnu_contract(n, g)
  rescue RuntimeError, KeyError
    rejected = true
  end
  raise "missing GNU negative regression rejection #{index}" unless rejected
end
puts 'shared Python GNU source/CPU/original-grant/consumer/release gates verified; 7 negative mutations rejected'
