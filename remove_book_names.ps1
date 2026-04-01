# 移除markdown文件中的书名信息
$files = Get-ChildItem -Path "d:\AI-Tutor-main\knowledge_base\question" -Recurse -Filter "*.md"

$totalFiles = $files.Count
$processedFiles = 0

Write-Host "开始处理 $totalFiles 个文件..."

foreach ($file in $files) {
    try {
        $content = Get-Content $file.FullName -Encoding UTF8 -Raw
        
        # 移除书名（使用正则表达式匹配书名号）
        $originalContent = $content
        $content = [System.Text.RegularExpressions.Regex]::Replace($content, '[《》]', '')
        
        if ($content -ne $originalContent) {
            Set-Content $file.FullName -Value $content -Encoding UTF8
            $processedFiles++
            Write-Host "处理: $($file.Name)"
        }
    } catch {
        Write-Host "处理 $($file.Name) 时出错: $($_.Exception.Message)"
    }
}

Write-Host "处理完成！共处理 $processedFiles 个文件。"
